#!/usr/bin/env bash
# start.sh — runs from repo root
set -o errexit

cd "$(dirname "$0")"

# Start Keep-Alive Service (prevents Render free tier sleep)
if [ -n "$RENDER_EXTERNAL_URL" ]; then
    echo "🏓 Starting Keep-Alive Service..."
    bash keep_alive.sh &
    KEEPALIVE_PID=$!
    echo "✅ Keep-Alive started with PID: $KEEPALIVE_PID"
fi

# Start Telegram Bot with auto-restart if it fails
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ "$TELEGRAM_BOT_TOKEN" != "your_token_here" ]; then
    echo "🤖 Starting Telegram Bot..."
    # Run bot in background with error handling
    while true; do
        python bot/telegram_bot.py 2>&1 | tee -a /tmp/bot.log || true
        echo "⚠️ Bot crashed, restarting in 5 seconds..."
        sleep 5
    done &
    BOT_PID=$!
    echo "✅ Bot started with PID: $BOT_PID"
else
    echo "⏭️ Telegram Bot disabled (no valid token)"
fi

echo "🚀 Starting Django Web Server on port ${PORT:-8000}..."
cd backend
exec gunicorn counselling_platform.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
