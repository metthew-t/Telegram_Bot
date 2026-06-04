#!/usr/bin/env bash
# start.sh — runs from repo root (called via: bash ../start.sh from backend/)
# Exit on error
set -o errexit

# Change to the directory where this script lives (repo root)
cd "$(dirname "$0")"

echo "Starting Telegram Bot in the background..."
python bot/telegram_bot.py &

echo "Starting Django Web Server on port ${PORT:-8000}..."
cd backend
exec gunicorn counselling_platform.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
