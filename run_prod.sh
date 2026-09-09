#!/bin/sh
set -e
cd "$(dirname "$0")"

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
elif [ -f venv/bin/activate ]; then
  . venv/bin/activate
fi

python manage.py prepare_prod
LISTEN="${WAITRESS_LISTEN:-0.0.0.0:8089}"

python serve.py &
python manage.py runbot
