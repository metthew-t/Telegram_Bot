#!/usr/bin/env bash
# keep_alive.sh - Pings the health endpoint every 5 minutes to keep Render awake

echo "🏓 Keep-Alive Service Started"
echo "Pinging health endpoint every 5 minutes to prevent sleep..."

while true; do
    sleep 300  # 5 minutes (more frequent to prevent 15-min timeout)
    
    # Get the current URL from environment or default
    BACKEND_URL="${RENDER_EXTERNAL_URL:-http://localhost:8000}"
    
    # Ping the health endpoint with timeout
    response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$BACKEND_URL/health/")
    
    if [ "$response" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Keep-alive ping successful (HTTP $response)"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Keep-alive ping failed (HTTP $response)"
    fi
done
