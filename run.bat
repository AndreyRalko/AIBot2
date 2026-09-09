@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo Starting Django admin at http://127.0.0.1:8089/  (development)
start "AIBot Django" cmd /k "python manage.py runserver 127.0.0.1:8089"

echo Starting Telegram bot...
start "AIBot Telegram" cmd /k "python manage.py runbot"
