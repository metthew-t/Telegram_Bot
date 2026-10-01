#!/usr/bin/env bash
# keep_alive.sh - Pings the health endpoint every 10 minutes to keep Render awake

echo "🏓 Keep-Alive Service Started"
echo "Pinging health endpoint every 10 minutes to prevent sleep..."

while true; do
    sleep 600  # 10 minutes
    
    # Get the current URL from environment or default
    BACKEND_URL="${RENDER_EXTERNAL_URL:-http://localhost:8000}"
    
    # Ping the health endpoint
    curl -s "$BACKEND_URL/health/" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Keep-alive ping successful"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Keep-alive ping failed"
    fi
done
