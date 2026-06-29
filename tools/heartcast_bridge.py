"""Bridge HeartCast BLE heart-rate notifications to the NutriMatch backend.

Expected flow:
Apple Watch -> HeartCast iPhone app -> BLE Heart Rate Service -> this script
-> POST /api/health/apple-watch/heart-rate -> NutriMatch dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience only
    load_dotenv = None

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
except ImportError:  # pragma: no cover - exercised manually when deps missing
    BleakClient = None
    BleakScanner = None
    BLEDevice = Any
    AdvertisementData = Any


HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
DEFAULT_URL = "http://127.0.0.1:8000/api/health/apple-watch/heart-rate"
DEFAULT_SOURCE = "apple_watch"


class HeartRateParseError(ValueError):
    """Raised when a BLE Heart Rate Measurement payload is malformed."""


@dataclass
class HeartRateSample:
    bpm: int
    measured_at: str
    source: str = DEFAULT_SOURCE


@dataclass
class BridgeConfig:
    url: str
    token: str
    device_name: str
    device_address: str | None
    scan_timeout: float
    min_send_interval: float


def parse_heart_rate_measurement(data: bytes) -> int:
    """Parse the standard BLE Heart Rate Measurement characteristic payload.

    The first byte is the flags field. If bit 0 is 0, BPM is an unsigned 8-bit
    integer in byte 1. If bit 0 is 1, BPM is an unsigned 16-bit little-endian
    integer in bytes 1 and 2. Optional trailing fields are ignored.
    """
    if len(data) < 2:
        raise HeartRateParseError("Heart Rate Measurement payload is too short")

    flags = data[0]
    value_is_uint16 = bool(flags & 0x01)
    if value_is_uint16:
        if len(data) < 3:
            raise HeartRateParseError("Heart Rate Measurement uint16 payload is too short")
        return int.from_bytes(data[1:3], byteorder="little", signed=False)

    return data[1]


def timestamp_now() -> str:
    """Return a timezone-aware ISO 8601 timestamp for the BLE notification time."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_uuid(value: str) -> str:
    return value.lower()


def service_uuids_from(device: BLEDevice, advertisement: AdvertisementData | None) -> list[str]:
    service_uuids = []
    if advertisement is not None:
        service_uuids.extend(getattr(advertisement, "service_uuids", None) or [])
    metadata = getattr(device, "metadata", None) or {}
    service_uuids.extend(metadata.get("uuids") or [])
    return sorted({normalize_uuid(uuid) for uuid in service_uuids})


def device_display_name(device: BLEDevice, advertisement: AdvertisementData | None) -> str:
    advertised_name = getattr(advertisement, "local_name", None) if advertisement is not None else None
    return advertised_name or getattr(device, "name", None) or "(no name)"


def device_rssi(device: BLEDevice, advertisement: AdvertisementData | None) -> Any:
    if advertisement is not None and getattr(advertisement, "rssi", None) is not None:
        return advertisement.rssi
    return getattr(device, "rssi", None)


def is_heartcast_candidate(
    device: BLEDevice,
    advertisement: AdvertisementData | None,
    preferred_name: str = "HeartCast",
) -> bool:
    name = device_display_name(device, advertisement).lower()
    uuids = service_uuids_from(device, advertisement)
    return HEART_RATE_SERVICE_UUID in uuids or preferred_name.lower() in name


def ensure_dependencies() -> None:
    if BleakScanner is None or BleakClient is None:
        raise SystemExit(
            "Missing dependency 'bleak'. Install the bridge dependencies first:\n"
            "  .\\.venv\\Scripts\\python.exe -m pip install -r requirements-heartcast.txt\n"
            "If this fails on Python 3.14, create a Python 3.12/3.13 venv for the bridge."
        )


def load_environment() -> None:
    if load_dotenv:
        load_dotenv()


def build_post_url(url: str, token: str) -> str:
    if "token=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}token={token}"


async def discover(timeout: float) -> list[tuple[BLEDevice, AdvertisementData | None]]:
    ensure_dependencies()
    try:
        result = await BleakScanner.discover(timeout=timeout, return_adv=True)
    except TypeError:
        devices = await BleakScanner.discover(timeout=timeout)
        return [(device, None) for device in devices]

    if isinstance(result, dict):
        return list(result.values())
    return [(device, None) for device in result]


async def scan_devices(timeout: float, preferred_name: str = "HeartCast") -> None:
    print(f"[BLE] Scanning for HeartCast / Heart Rate Service for {timeout:g}s...")
    devices = await discover(timeout)
    if not devices:
        print("[BLE] No BLE devices found.")
        return

    for device, advertisement in devices:
        name = device_display_name(device, advertisement)
        address = getattr(device, "address", "(no address)")
        rssi = device_rssi(device, advertisement)
        uuids = service_uuids_from(device, advertisement)
        candidate = is_heartcast_candidate(device, advertisement, preferred_name)
        marker = "MATCH" if candidate else "----"
        print(f"[{marker}] name={name} address={address} rssi={rssi}")
        print(f"       service_uuids={uuids or []}")


async def find_device(config: BridgeConfig) -> BLEDevice | None:
    print("[BLE] Scanning for HeartCast...")
    devices = await discover(config.scan_timeout)
    if not devices:
        return None

    configured_address = config.device_address.lower() if config.device_address else None
    configured_name = config.device_name.lower()

    if configured_address:
        for device, advertisement in devices:
            address = (getattr(device, "address", "") or "").lower()
            if address == configured_address:
                print(f"[BLE] Found configured device at {device.address}")
                return device
        print("[BLE] Configured address was not found in this scan; falling back to Heart Rate Service/name matching")

    service_matches = []
    name_matches = []
    for device, advertisement in devices:
        name = device_display_name(device, advertisement)
        uuids = service_uuids_from(device, advertisement)
        if HEART_RATE_SERVICE_UUID in uuids:
            service_matches.append((device, advertisement))
        if configured_name and configured_name in name.lower():
            name_matches.append((device, advertisement))

    selected = service_matches[0] if service_matches else (name_matches[0] if name_matches else None)
    if not selected:
        return None

    device, advertisement = selected
    print(f"[BLE] Found {device_display_name(device, advertisement)} at {device.address}")
    return device


class HeartCastBridge:
    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self.queue: asyncio.Queue[HeartRateSample] = asyncio.Queue(maxsize=200)
        self.stop_event = asyncio.Event()
        self.connected_event = asyncio.Event()
        self.http_client: httpx.AsyncClient | None = None
        self.client: BleakClient | None = None
        self.last_sent_at = 0.0

    async def run(self) -> None:
        ensure_dependencies()
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        post_worker = asyncio.create_task(self.post_worker())
        try:
            await self.reconnect_loop()
        finally:
            self.stop_event.set()
            post_worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await post_worker
            if self.client and self.client.is_connected:
                with contextlib.suppress(Exception):
                    await self.client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
                with contextlib.suppress(Exception):
                    await self.client.disconnect()
            if self.http_client:
                await self.http_client.aclose()

    async def reconnect_loop(self) -> None:
        backoffs = [1, 2, 5, 10]
        attempt = 0
        while not self.stop_event.is_set():
            device = await find_device(self.config)
            if not device:
                delay = backoffs[min(attempt, len(backoffs) - 1)]
                print(f"[BLE] HeartCast not found, rescanning in {delay}s...")
                attempt += 1
                await asyncio.sleep(delay)
                continue

            try:
                attempt = 0
                await self.connect_and_stream(device)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                delay = backoffs[min(attempt, len(backoffs) - 1)]
                attempt += 1
                print(f"[BLE] Connection error: {exc}. Reconnecting in {delay}s...")
                await asyncio.sleep(delay)

    async def connect_and_stream(self, device: BLEDevice) -> None:
        self.connected_event.clear()

        def disconnected_callback(_client: BleakClient) -> None:
            print("[BLE] Connection lost")
            self.connected_event.clear()

        async with BleakClient(device, disconnected_callback=disconnected_callback) as client:
            self.client = client
            print("[BLE] Connected")
            self.connected_event.set()

            if hasattr(client, "get_services"):
                services = await client.get_services()
            else:
                services = client.services
            characteristic = services.get_characteristic(HEART_RATE_MEASUREMENT_UUID)
            if characteristic is None:
                raise RuntimeError("Heart Rate Measurement characteristic 0x2A37 not found")

            def handle_notification(_sender: Any, data: bytearray) -> None:
                try:
                    bpm = parse_heart_rate_measurement(bytes(data))
                    sample = HeartRateSample(bpm=bpm, measured_at=timestamp_now())
                    self.queue.put_nowait(sample)
                    print(f"[HR] {sample.bpm} BPM at {sample.measured_at}")
                except asyncio.QueueFull:
                    print("[HR] Queue is full, dropping one sample")
                except Exception as exc:
                    print(f"[HR] Could not parse notification {bytes(data).hex()}: {exc}")

            await client.start_notify(characteristic, handle_notification)
            print("[BLE] Subscribed to Heart Rate Measurement")

            while client.is_connected and not self.stop_event.is_set():
                await asyncio.sleep(0.5)

            with contextlib.suppress(Exception):
                await client.stop_notify(characteristic)

    async def post_worker(self) -> None:
        assert self.http_client is not None
        post_url = build_post_url(self.config.url, self.config.token)

        while not self.stop_event.is_set():
            sample = await self.queue.get()
            try:
                now = asyncio.get_running_loop().time()
                wait_for = self.config.min_send_interval - (now - self.last_sent_at)
                if wait_for > 0:
                    await asyncio.sleep(wait_for)

                payload = {
                    "bpm": sample.bpm,
                    "measured_at": sample.measured_at,
                    "source": sample.source,
                }
                response = await self.http_client.post(post_url, json=payload)
                self.last_sent_at = asyncio.get_running_loop().time()
                if 200 <= response.status_code < 300:
                    print(f"[HTTP] POST {response.status_code}")
                else:
                    print(f"[HTTP] POST {response.status_code}: {response.text[:500]}")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[HTTP] POST failed: {exc}")
            finally:
                self.queue.task_done()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HeartCast BLE -> NutriMatch heart-rate bridge")
    parser.add_argument("--scan", action="store_true", help="Scan BLE devices and print HeartCast candidates")
    parser.add_argument("--url", default=os.getenv("NUTRIMATCH_HEART_RATE_URL", DEFAULT_URL))
    parser.add_argument("--token", default=os.getenv("NUTRIMATCH_HEART_RATE_TOKEN", ""))
    parser.add_argument("--device-name", default=os.getenv("HEARTCAST_DEVICE_NAME", "HeartCast"))
    parser.add_argument("--device-address", default=os.getenv("HEARTCAST_DEVICE_ADDRESS"))
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    parser.add_argument("--min-send-interval", type=float, default=0.0)
    return parser.parse_args(argv)


async def async_main(argv: list[str]) -> int:
    load_environment()
    args = parse_args(argv)
    ensure_dependencies()

    if args.scan:
        await scan_devices(args.scan_timeout, args.device_name)
        return 0

    if not args.token and "token=" not in args.url:
        raise SystemExit(
            "Missing token. Set NUTRIMATCH_HEART_RATE_TOKEN or pass --token.\n"
            "For the local demo use: --token apple-watch-demo-2026"
        )

    config = BridgeConfig(
        url=args.url,
        token=args.token,
        device_name=args.device_name,
        device_address=args.device_address,
        scan_timeout=args.scan_timeout,
        min_send_interval=max(0.0, args.min_send_interval),
    )

    bridge = HeartCastBridge(config)
    try:
        await bridge.run()
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped by user")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        return asyncio.run(async_main(argv))
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped by user")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
