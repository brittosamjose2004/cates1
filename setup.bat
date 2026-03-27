@echo off
setlocal enabledelayedexpansion

echo === Step 1: Check if .venv exists ===
if exist .venv (
    echo .venv exists
    set VENV_EXISTS=1
) else (
    echo .venv missing
    set VENV_EXISTS=0
)

if !VENV_EXISTS! equ 0 (
    echo.
    echo === Step 2: Creating .venv ===
    python -m venv .venv
    echo .venv created
)

echo.
echo === Step 3: Activate venv and install requirements ===
call .\\.venv\\Scripts\\activate.bat
pip install -r backend\requirements.txt

echo.
echo === Setup complete ===
