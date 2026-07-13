#!/bin/bash
# Dijital Varlik — Tek Komutla Her Şeyi Başlat
# Auto-detect Windows IP (WSL2 NAT modu)
export WINDOWS_HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "9Router: $WINDOWS_HOST_IP:20128"

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

# Dashboard + WebSocket
necho ">> Telegram bot baslatiliyor..."
TELEGRAM_BOT_TOKEN="8903802500:AAH7hMaIFMa86LCLxkEeN8NlLD5rIZdhneo" nohup python3 -u mudahale/openclaw_bridge.py > /tmp/tg_bot.log 2>&1 &
BOT_PID=$!
echo ">> Nano Matris başlatılıyor (port 9998)..."
python3 dashboard/server.py 9998 &
DASH_PID=$!

echo ">> WebSocket backend başlatılıyor (port 8000)..."
python3 wsl_backend/main.py 8000 &
WS_PID=$!
sleep 1

echo ""
echo "============================================"
echo "  HAZIR!"
echo "  Nano Matris: http://localhost:8000"
echo "  Dashboard:   http://localhost:9998"
necho ">> Telegram bot baslatiliyor..."
TELEGRAM_BOT_TOKEN="8903802500:AAH7hMaIFMa86LCLxkEeN8NlLD5rIZdhneo" nohup python3 -u mudahale/openclaw_bridge.py > /tmp/tg_bot.log 2>&1 &
BOT_PID=$!
echo "  VS Code:     http://localhost:8080"
echo "  Chat:        http://localhost:3000"
echo "============================================"
echo "  Çıkmak için: kill $DASH_PID $WS_PID $BOT_PID"
echo "============================================"

wait $DASH_PID $WS_PID
