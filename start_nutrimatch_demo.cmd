@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "ROOT=%CD%"
set "BACKEND_PY=%ROOT%\.venv\Scripts\python.exe"
set "HEARTCAST_PY=%ROOT%\.venv-heartcast-py314\Scripts\python.exe"
set "FRONTEND_DIR=%ROOT%\frontend"
set "HEARTCAST_TOKEN=apple-watch-demo-2026"

title NutriMatch Demo Launcher

echo.
echo ========================================
echo   NutriMatch Demo Launcher
echo ========================================
echo.

if not exist "%BACKEND_PY%" (
  echo [ERROR] Backend Python wurde nicht gefunden:
  echo         %BACKEND_PY%
  echo.
  echo Bitte zuerst die Backend-venv vorbereiten.
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [ERROR] Frontend node_modules wurde nicht gefunden.
  echo.
  echo Bitte einmal ausfuehren:
  echo   cd frontend
  echo   npm.cmd install
  echo.
  pause
  exit /b 1
)

echo [1/4] Starte Backend auf http://localhost:8000 ...
start "NutriMatch Backend" cmd /k "cd /d "%ROOT%" && "%BACKEND_PY%" -m backend.seed_data && "%BACKEND_PY%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/4] Starte Frontend auf http://localhost:5173 ...
start "NutriMatch Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm.cmd run dev -- --host 0.0.0.0"

timeout /t 2 /nobreak >nul

if exist "%HEARTCAST_PY%" (
  echo [3/4] Starte HeartCast BLE Bridge fuer Apple Watch ...
  start "NutriMatch HeartCast Bridge" cmd /k "cd /d "%ROOT%" && "%HEARTCAST_PY%" tools\heartcast_bridge.py --token %HEARTCAST_TOKEN%"
) else (
  echo [3/4] HeartCast Bridge uebersprungen: .venv-heartcast-py314 nicht gefunden.
)

echo [4/4] Oeffne Browser ...
timeout /t 6 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo Fertig. Es wurden separate Fenster fuer Backend, Frontend und optional HeartCast geoeffnet.
echo.
echo Fuer Apple Watch Live-Puls:
echo   1. HeartCast auf iPhone und Apple Watch oeffnen.
echo   2. Auf der Apple Watch Start druecken.
echo   3. Im Fenster "NutriMatch HeartCast Bridge" auf [HR] ... und [HTTP] POST 200 achten.
echo.
echo Dieses Launcher-Fenster kann geschlossen werden.
echo.
pause

