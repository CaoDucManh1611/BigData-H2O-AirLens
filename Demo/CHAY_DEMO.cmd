@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "AIR_PYTHON=C:\Users\DUC_STRONG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%AIR_PYTHON%" (
  echo Khong tim thay Python. Hay cai Python 3 hoac sua duong dan AIR_PYTHON trong file nay.
  pause
  exit /b 1
)
start "AirLens" http://127.0.0.1:8766
"%AIR_PYTHON%" -X utf8 server.py
pause
