#!/bin/bash
# Dijital Varlik — Tek Komutla Her Şeyi Başlat
cd "$(dirname "$0")"
source .venv/bin/activate

echo "============================================"
echo "  DİJİTAL VARLIK BAŞLATILIYOR"
echo "============================================"

# Docker servisleri
echo ">> Docker servisleri..."
docker start browserless 2>/dev/null || docker run -d --name browserless --restart=always -p 3004:3000 browserless/chrome
docker start dijital-varlik_litellm_1 2>/dev/null || true

# 9router kontrol
echo ">> 9router kontrol..."
WIN_IP=$(ip route show default 2>/dev/null | awk '{print $3}')
if curl -s --max-time 2 "http://${WIN_IP:-172.23.96.1}:20128/api/health" > /dev/null 2>&1; then
    echo "   9router: AKTIF (${WIN_IP:-172.23.96.1}:20128)"
else
    echo "   ⚠️  9router KAPALI! Windows'ta başlat: Hide to Tray"
fi

# Dashboard
echo ">> Dashboard başlatılıyor (port 9998)..."
python3 dashboard/server.py 9998 &
DASH_PID=$!
sleep 1

echo ""
echo "============================================"
echo "  HAZIR!"
echo "  Dashboard: http://localhost:9998"
echo "  VS Code:   http://localhost:8080"
echo "  Chat:      http://localhost:3000"
echo "============================================"
echo "  Çıkmak için: kill $DASH_PID"
echo "============================================"

wait $DASH_PID
