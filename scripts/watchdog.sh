#!/bin/bash
# 9router Watchdog — 10 saniyede bir kontrol, düşerse kaldırır
while true; do
    if ! curl -s --max-time 3 http://localhost:20128/api/health > /dev/null 2>&1; then
        echo "[$(date)] 9router KAPALI!"
    fi
    sleep 10
done
