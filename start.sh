#!/usr/bin/env bash
# start.sh
# Exit on error
set -o errexit

echo "Starting Telegram Bot in the background..."
python bot/telegram_bot.py &

echo "Starting Django Web Server..."
gunicorn counselling_platform.wsgi:application
