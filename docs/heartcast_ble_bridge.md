# HeartCast BLE Bridge für NutriMatch auf Windows

Diese Integration ersetzt den iPhone-Kurzbefehl nicht komplett, sondern ergänzt ihn als Live-Variante:

```text
Apple Watch → HeartCast auf dem iPhone → Bluetooth LE → Python bridge auf Windows → NutriMatch backend → Dashboard
```

Der bestehende Shortcut-POST bleibt als Fallback erhalten.

## Voraussetzungen

- Apple Watch ist mit dem iPhone gekoppelt.
- HeartCast ist auf iPhone/Apple Watch installiert.
- Bluetooth ist auf dem Windows-Laptop aktiviert.
- NutriMatch backend läuft auf dem Laptop.

## Installation

Aus dem Projektordner:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python -m pip install -r requirements-heartcast.txt
```

Hinweis zu Python 3.14: ältere `bleak`-Versionen `<1.0` unterstützen Python 3.14 nicht. Deshalb verwendet `requirements-heartcast.txt` eine aktuelle `bleak`-Version. Falls `bleak` oder Windows-Bluetooth-Abhängigkeiten trotzdem Probleme machen, nutze für den Bridge-Prozess ein separates Python 3.12/3.13 venv. Das backend kann trotzdem mit der bestehenden Projekt-venv laufen.

## Backend starten

```powershell
.\.venv\Scripts\python.exe start.py
```

Der Standard-POST des Bridges ist:

```text
http://127.0.0.1:8000/api/health/apple-watch/heart-rate?token=apple-watch-demo-2026
```

Wenn backend auf einer anderen Adresse läuft, setze die URL explizit:

```powershell
$env:NUTRIMATCH_HEART_RATE_URL="http://127.0.0.1:8000/api/health/apple-watch/heart-rate"
$env:NUTRIMATCH_HEART_RATE_TOKEN="apple-watch-demo-2026"
```

## HeartCast starten

1. HeartCast auf iPhone und Apple Watch öffnen.
2. Auf der Apple Watch `Start` drücken.
3. HeartCast auf dem iPhone beim ersten BLE-Verbindungsaufbau offen lassen.
4. HeartCast nicht manuell im normalen Windows-Bluetooth-Menü koppeln, außer Windows/HeartCast verlangt es ausdrücklich.

## BLE-Geräte scannen

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --scan
```

Die Ausgabe zeigt Gerätenamen, Bluetooth-Adresse, RSSI, advertised service UUIDs und `MATCH`, wenn Heart Rate Service `0000180d-0000-1000-8000-00805f9b34fb` oder ein HeartCast-Name erkannt wurde.

## Bridge starten

Automatische Suche:

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --token apple-watch-demo-2026
```

Mit Gerätename:

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --device-name HeartCast --token apple-watch-demo-2026
```

Mit Bluetooth-Adresse aus dem Scan:

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --device-address "XX:XX:XX:XX:XX:XX" --token apple-watch-demo-2026
```

Hinweis: iPhone/HeartCast kann wegen BLE Privacy rotierende Adressen verwenden. Wenn eine zuvor gefundene Adresse später nicht mehr auftaucht, fällt der Bridge automatisch auf Heart Rate Service/name matching zurück. Für die Präsentation ist meistens der automatische Start ohne `--device-address` am stabilsten.

Mit expliziter backend URL:

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --url "http://127.0.0.1:8000/api/health/apple-watch/heart-rate" --token "apple-watch-demo-2026"
```

Optionales Rate Limit, falls HeartCast sehr viele Notifications sendet:

```powershell
.\.venv\Scripts\python.exe tools\heartcast_bridge.py --token apple-watch-demo-2026 --min-send-interval 1.0
```

## Erwartete Logs

```text
[BLE] Scanning for HeartCast...
[BLE] Found HeartCast-AB12 at XX:XX:XX:XX:XX:XX
[BLE] Connected
[BLE] Subscribed to Heart Rate Measurement
[HR] 91 BPM at 2026-06-29T10:11:25+02:00
[HTTP] POST 200
```

Dashboard öffnen:

```text
http://localhost:5173/health/watch/latest
```

Sobald BLE Notifications ankommen, sollte der BPM-Wert ohne manuelles Reload innerhalb weniger Sekunden aktualisiert werden.

## Troubleshooting

### HeartCast wird nicht gefunden

- HeartCast auf iPhone und Apple Watch öffnen.
- Auf der Watch `Start` drücken.
- Noch einmal `--scan` ausführen.
- Falls ein Gerät ohne Namen, aber mit Heart Rate Service erscheint, dessen Adresse mit `--device-address` verwenden.

### Bluetooth ist aus oder gesperrt

- Windows Bluetooth aktivieren.
- Prüfen, ob andere Apps den Adapter blockieren.
- Bei `access denied` PowerShell/Terminal neu öffnen; notfalls als Administrator testen.

### HeartCast geht in den Hintergrund

- iPhone entsperrt lassen.
- HeartCast während des ersten Verbindungsaufbaus im Vordergrund lassen.

### Windows sieht keinen Heart Rate Service

- HeartCast neu starten.
- Bluetooth am Laptop kurz aus/an.
- `--scan-timeout 15` verwenden.

### Connection timeout

- Abstand zwischen iPhone und Laptop reduzieren.
- Bridge neu starten.
- Mit `--device-address` verbinden.

### Backend nicht erreichbar

- Prüfen, ob `start.py` läuft.
- Im Browser testen: `http://127.0.0.1:8000/docs`.
- Falls backend nicht lokal läuft, `NUTRIMATCH_HEART_RATE_URL` oder `--url` anpassen.

### Falscher Token

- Bridge loggt dann typischerweise `POST 403`.
- Token muss zum backend `APPLE_WATCH_DEMO_TOKEN` passen.

### Python 3.14 dependency issue

- Ältere `bleak<1.0` Releases unterstützen Python 3.14 nicht.
- Wenn `pip install -r requirements-heartcast.txt` trotzdem mit `bleak` scheitert, Python 3.12/3.13 installieren und nur für den Bridge ein separates venv erstellen.
