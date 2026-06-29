import hashlib
import hmac
import html
import logging
import os
import random
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, HealthData
from backend.schemas import AppleWatchHeartRateSubmit, HealthDataSubmit
from backend.config import APPLE_WATCH_DEMO_TOKEN
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/health", tags=["health"])
logger = logging.getLogger("nutrimatch.apple_watch")

NFC_DEMO_TOKEN = os.getenv("NFC_DEMO_TOKEN", "nutrimatch-demo-2026")
NFC_EVENT_TTL = timedelta(minutes=10)
_nfc_events: list[dict] = []
_nfc_lock = Lock()
APPLE_WATCH_SAMPLE_TTL = timedelta(minutes=15)
_apple_watch_samples: list[dict] = []
_apple_watch_last_sync: dict | None = None
_apple_watch_lock = Lock()


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _apple_watch_sample_key(source: str, measured_at: datetime, bpm: int) -> tuple[str, str, int]:
    return (source.strip().lower(), _as_utc(measured_at).isoformat(), bpm)


def _serialize_apple_watch_sample(sample: dict) -> dict:
    return {
        **sample,
        "measured_at": _as_utc(sample["measured_at"]).isoformat(),
        "received_at": _as_utc(sample["received_at"]).isoformat(),
        "last_received_at": _as_utc(sample.get("last_received_at", sample["received_at"])).isoformat(),
    }


def _generate_watch_history(device_id: str) -> list[dict]:
    """Create stable, correlated demo data for today and the previous 13 days."""
    today = datetime.now().date()
    seed = int(hashlib.sha256(f"{device_id}:{today.isoformat()}".encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    history = []

    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        weekend = day.weekday() >= 5
        sleep_hours = _clamp(6.45 + (0.55 if weekend else 0) + rng.gauss(0, 0.65), 4.8, 8.4)
        sleep_quality = round(_clamp(47 + sleep_hours * 7 + rng.gauss(0, 5), 48, 94))
        steps = round(_clamp(7200 + (1100 if weekend else 0) + rng.gauss(0, 1850), 2900, 13200))
        active_minutes = round(_clamp(12 + steps / 290 + rng.gauss(0, 7), 14, 78))
        resting_heart_rate = round(_clamp(72 - sleep_hours * 0.85 - active_minutes * 0.035 + rng.gauss(0, 2), 57, 76))
        active_calories = round(_clamp(steps * 0.031 + active_minutes * 2.4 + rng.gauss(0, 24), 160, 690))

        history.append({
            "date": day.isoformat(),
            "steps": steps,
            "sleep_hours": round(sleep_hours, 2),
            "sleep_quality": sleep_quality,
            "resting_heart_rate": resting_heart_rate,
            "active_minutes": active_minutes,
            "active_calories": active_calories,
        })

    # Make today's headline values predictable for the physical demo.
    history[-1].update({
        "steps": 8432,
        "sleep_hours": 5.7,
        "sleep_quality": 61,
        "resting_heart_rate": 67,
        "active_minutes": 38,
        "active_calories": 352,
    })
    return history


def _watch_payload(history: list[dict], device_id: str, synced_at: datetime, event_id: str = "latest") -> dict:
    averages = {
        "steps": round(sum(day["steps"] for day in history) / len(history)),
        "sleep_hours": round(sum(day["sleep_hours"] for day in history) / len(history), 2),
        "resting_heart_rate": round(sum(day["resting_heart_rate"] for day in history) / len(history)),
        "active_minutes": round(sum(day["active_minutes"] for day in history) / len(history)),
    }
    return {
        "event_id": event_id,
        "device": {
            "id": device_id,
            "name": "NutriMatch Demo Watch",
            "battery": 78,
            "connection": "NFC",
            "synced_at": synced_at.isoformat(),
        },
        "history": history,
        "today": history[-1],
        "averages": averages,
        "live_heart_rate": 72,
        "simulated": True,
    }


def _get_nfc_event(event_id: str) -> dict | None:
    cutoff = datetime.utcnow() - NFC_EVENT_TTL
    with _nfc_lock:
        _nfc_events[:] = [event for event in _nfc_events if event["created_at"] >= cutoff]
        return next((event.copy() for event in _nfc_events if event["id"] == event_id), None)


def _latest_apple_watch_sample() -> dict | None:
    cutoff = _utc_now() - APPLE_WATCH_SAMPLE_TTL
    with _apple_watch_lock:
        global _apple_watch_last_sync
        _apple_watch_samples[:] = [
            sample for sample in _apple_watch_samples
            if _as_utc(sample.get("last_received_at", sample["received_at"])) >= cutoff
        ]
        if not _apple_watch_samples:
            _apple_watch_last_sync = None
            return None
        sample = max(
            _apple_watch_samples,
            key=lambda item: (
                _as_utc(item["measured_at"]),
                _as_utc(item.get("last_received_at", item["received_at"])),
                item["id"],
            ),
        )
        latest = _serialize_apple_watch_sample(sample.copy())
        if _apple_watch_last_sync:
            latest["sync_received_at"] = _as_utc(_apple_watch_last_sync["received_at"]).isoformat()
            latest["last_post"] = {
                "bpm": _apple_watch_last_sync["bpm"],
                "measured_at": _as_utc(_apple_watch_last_sync["measured_at"]).isoformat(),
                "received_at": _as_utc(_apple_watch_last_sync["received_at"]).isoformat(),
                "source": _apple_watch_last_sync["source"],
                "duplicate": _apple_watch_last_sync["duplicate"],
            }
        return latest


@router.get("/nfc/tap", response_class=HTMLResponse)
def tap_nfc_device(
    device: str = Query(default="NM-WATCH-01", min_length=3, max_length=64),
    token: str = Query(default=""),
):
    """Public landing endpoint stored on the physical NDEF tag."""
    if not hmac.compare_digest(token, NFC_DEMO_TOKEN):
        raise HTTPException(status_code=403, detail="Ungültiger NFC-Tag")

    event = {
        "id": uuid4().hex,
        "device_id": device,
        "device_name": "NutriMatch Demo Watch",
        "created_at": datetime.utcnow(),
    }
    with _nfc_lock:
        _nfc_events.append(event)
        del _nfc_events[:-20]

    safe_device = html.escape(device)
    return HTMLResponse(f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NutriMatch Watch</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#f1f8f4;font-family:Inter,system-ui,sans-serif;color:#1b4332}}
.card{{width:min(86vw,380px);background:white;border:1px solid #d8eadf;border-radius:24px;padding:38px 28px;text-align:center;box-shadow:0 18px 55px rgba(27,67,50,.13)}}
.icon{{width:72px;height:72px;margin:0 auto 18px;border-radius:50%;display:grid;place-items:center;background:#d8f3dc;font-size:36px}}
h1{{font-size:24px;margin:0 0 8px}}p{{color:#52705f;margin:6px 0}}.ok{{display:inline-block;margin-top:22px;padding:10px 16px;border-radius:999px;background:#2d6a4f;color:white;font-weight:700}}
small{{display:block;margin-top:22px;color:#82958a}}
</style></head><body><main class="card"><div class="icon">✓</div><h1>Gerät erkannt</h1>
<p><strong>{safe_device}</strong></p><p>14 Tage Gesundheitsdaten wurden sicher an NutriMatch übertragen.</p>
<span class="ok">Synchronisierung erfolgreich</span><small>Dieses Fenster kann geschlossen werden.</small></main></body></html>""")


@router.get("/nfc/events/latest")
def latest_nfc_event(
    after: str | None = None,
    current_user: User = Depends(get_current_user),
):
    cutoff = datetime.utcnow() - NFC_EVENT_TTL
    with _nfc_lock:
        recent = [event for event in _nfc_events if event["created_at"] >= cutoff]
        if after:
            last_seen_index = next(
                (index for index, event in enumerate(recent) if event["id"] == after),
                -1,
            )
            candidates = recent[last_seen_index + 1:]
        else:
            candidates = recent[-1:]
        if not candidates:
            return {"event": None}
        event = candidates[-1]
        return {"event": {**event, "created_at": event["created_at"].isoformat()}}


@router.post("/nfc/events/{event_id}/connect")
def connect_nfc_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_nfc_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="NFC-Synchronisierung ist abgelaufen")

    history = _generate_watch_history(event["device_id"])

    # A repeated tap is a sync, not a duplicate import.
    db.query(HealthData).filter(
        HealthData.user_id == current_user.id,
        HealthData.source == "nfc_demo_watch",
        HealthData.data_type == "wearable_daily_summary",
    ).delete(synchronize_session=False)

    for day in history:
        recorded_at = datetime.fromisoformat(f"{day['date']}T20:00:00")
        db.add(HealthData(
            user_id=current_user.id,
            source="nfc_demo_watch",
            data_type="wearable_daily_summary",
            value={
                **day,
                "device_id": event["device_id"],
                "simulated": True,
                "sync_event_id": event_id,
            },
            recorded_at=recorded_at,
        ))
    db.commit()

    return _watch_payload(history, event["device_id"], datetime.utcnow(), event_id)


@router.get("/nfc/device/latest")
def get_latest_nfc_device(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reopen the latest persisted watch dashboard without a live NFC event."""
    entries = (
        db.query(HealthData)
        .filter(
            HealthData.user_id == current_user.id,
            HealthData.source == "nfc_demo_watch",
            HealthData.data_type == "wearable_daily_summary",
        )
        .order_by(HealthData.recorded_at.asc())
        .all()
    )
    if not entries:
        raise HTTPException(status_code=404, detail="Keine gespeicherten Wearable-Daten gefunden")

    history = [entry.value for entry in entries[-14:] if entry.value]
    if not history:
        raise HTTPException(status_code=404, detail="Keine gespeicherten Wearable-Daten gefunden")

    latest_entry = entries[-1]
    device_id = history[-1].get("device_id", "NM-WATCH-01")
    synced_at = latest_entry.created_at or latest_entry.recorded_at or datetime.utcnow()
    return _watch_payload(history, device_id, synced_at)


@router.post("/apple-watch/heart-rate")
def receive_apple_watch_heart_rate(
    payload: AppleWatchHeartRateSubmit,
    token: str = Query(default=""),
):
    """Receive the latest heart-rate sample from an iPhone Shortcut/Kurzbefehl."""
    global _apple_watch_last_sync
    if not hmac.compare_digest(token, APPLE_WATCH_DEMO_TOKEN):
        raise HTTPException(status_code=403, detail="Ungültiger Apple-Watch-Demo-Token")

    now = _utc_now()
    measured_at = _as_utc(payload.measured_at or now)
    bpm = round(payload.bpm)
    source = payload.source or "Apple Watch"
    sample_key = _apple_watch_sample_key(source, measured_at, bpm)
    sample = {
        "id": uuid4().hex,
        "bpm": bpm,
        "source": source,
        "measured_at": measured_at,
        "received_at": now,
        "last_received_at": now,
        "sync_count": 1,
    }

    with _apple_watch_lock:
        existing = next(
            (
                item for item in _apple_watch_samples
                if _apple_watch_sample_key(item["source"], item["measured_at"], item["bpm"]) == sample_key
            ),
            None,
        )
        duplicate = existing is not None
        if existing:
            existing["last_received_at"] = now
            existing["sync_count"] = existing.get("sync_count", 1) + 1
            stored_sample = existing
            action = "updated_duplicate"
        else:
            _apple_watch_samples.append(sample)
            stored_sample = sample
            action = "created_new"
        del _apple_watch_samples[:-60]
        _apple_watch_last_sync = {
            "bpm": bpm,
            "source": source,
            "measured_at": measured_at,
            "received_at": now,
            "duplicate": duplicate,
            "action": action,
        }

    logger.warning(
        "[TEMP Apple Watch POST] bpm=%s measured_at=%s source=%s received_at=%s action=%s duplicate=%s",
        bpm,
        measured_at.isoformat(),
        source,
        now.isoformat(),
        action,
        duplicate,
    )

    return {
        "status": "duplicate_updated" if duplicate else "saved",
        "action": action,
        "duplicate": duplicate,
        "sample": _serialize_apple_watch_sample(stored_sample.copy()),
    }


@router.get("/apple-watch/heart-rate/latest")
def get_latest_apple_watch_heart_rate(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """Expose the latest received Apple Watch heart-rate value to the logged-in demo UI."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return {"sample": _latest_apple_watch_sample(), "server_time": _utc_now().isoformat()}


@router.post("/data")
def submit_health_data(
    data: HealthDataSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    health_entry = HealthData(
        user_id=current_user.id,
        source=data.source,
        data_type=data.data_type,
        value=data.value,
        recorded_at=data.recorded_at or datetime.utcnow(),
    )
    db.add(health_entry)
    db.commit()
    db.refresh(health_entry)
    return {"status": "saved", "id": health_entry.id}


@router.get("/data")
def get_my_health_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(HealthData)
        .filter(HealthData.user_id == current_user.id)
        .order_by(HealthData.recorded_at.desc())
        .limit(50)
        .all()
    )
