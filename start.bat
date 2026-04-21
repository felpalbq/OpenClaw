@echo off
REM OpenClaw startup — sets PYTHONPATH and launches the system
REM Requires: Python 3.10+, ahri/ repo cloned alongside openclaw/

set "OPENCLAW_DIR=%~dp0"
set "AHRI_DIR=%OPENCLAW_DIR%..\ahri"

REM Add both openclaw and ahri to Python path
set "PYTHONPATH=%OPENCLAW_DIR%;%AHRI_DIR%"

REM Load .env if present
if exist "%OPENCLAW_DIR%.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%OPENCLAW_DIR%.env") do (
        set "%%a=%%b"
    )
)

echo Starting OpenClaw...
python -m scheduler