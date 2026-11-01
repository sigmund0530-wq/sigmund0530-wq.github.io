@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -m pip install -r requirements.txt
  start "" http://127.0.0.1:8766
  py server.py
) else (
  python -m pip install -r requirements.txt
  start "" http://127.0.0.1:8766
  python server.py
)
pause
