@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo Preparing production...
python manage.py prepare_prod
if errorlevel 1 (
  echo Production check failed.
  exit /b 1
)

echo Starting Waitress at http://0.0.0.0:8089/
start "AIBot Web" cmd /k "python serve.py"

echo Starting Telegram bot...
start "AIBot Telegram" cmd /k "python manage.py runbot"
