@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo Starting Django admin at http://127.0.0.1:8000/
start "AIBot Django" cmd /k "python manage.py runserver"

echo Starting Telegram bot...
start "AIBot Telegram" cmd /k "python manage.py runbot"
