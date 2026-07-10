#!/usr/bin/env python3
"""
NANO MATRIX WebSocket Backend — Dijital Varlik Komut Merkezi.

Frontend'den gelen komutları alır, Mahkeme + smolagents + BrowserUse zincirine iletir,
sonuçları gerçek zamanlı WebSocket üzerinden döndürür.

Başlat: python3 wsl_backend/main.py
Port: 8000 (WebSocket + HTTP)
"""
import asyncio, json, sys, os, traceback, subprocess, threading
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
VENV = str(ROOT / ".venv" / "bin" / "python3")
sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="OTONOM KOR — NANO MATRIS")

# Frontend'i serve et
FRONTEND = ROOT / "dashboard" / "nano_matrix.html"
if not FRONTEND.exists():
    FRONTEND = ROOT / "wsl_backend" / "index.html"


class ConnectionManager:
    def __init__(self): self.active = set()
    async def connect(self, ws): self.active.add(ws)
    def disconnect(self, ws): self.active.discard(ws)
    async def send(self, ws, data): await ws.send_text(json.dumps(data, ensure_ascii=False))
    async def broadcast(self, data):
        for ws in list(self.active):
            try: await ws.send_text(json.dumps(data, ensure_ascii=False))
            except: self.active.discard(ws)

mgr = ConnectionManager()


def otonom_isle(komut: str) -> str:
    """Komutu otonom.py ile işle."""
    komut_lower = komut.lower().strip()

    # Basit cevaplar (9Router'siz, anında)
    basit_cevaplar = {
        "saat": lambda: f"Saat: {datetime.now().strftime('%H:%M:%S')}",
        "tarih": lambda: f"Tarih: {datetime.now().strftime('%d.%m.%Y')}",
        "merhaba": lambda: "Merhaba Mösyö. Dijital Varlık Nano Matris emrinizde.",
        "nasılsın": lambda: "Tüm sistemler nominal. Mahkeme aktif, Kesici tetikte. Emrinizi bekliyorum.",
        "kimsin": lambda: "Ben Dijital Varlık — 4 Mahkeme rolü, 6 zincir, 75 AI model ile çalışan otonom organizma.",
        "yardım": lambda: "KOMUTLAR: saat, tarih, ara [konu], kod [görev], web [url], yüz [fotoğraf], ekran",
        "selam": lambda: "Selam Mösyö. Nano Matris bağlantısı stabil.",
        "durum": lambda: _sistem_durumu(),
    }
    for k, v in basit_cevaplar.items():
        if komut_lower == k or komut_lower.startswith(k):
            return v()

    # 9Router + smolagents zinciri
    try:
        from altyapi.kesici import kesici
        local = kesici.tani(komut)
        if local: return local
    except: pass

    try:
        from altyapi.litellm_bridge import litellm
        r = litellm.chat([{"role":"user","content":komut}], max_tokens=300)
        if r and r.get("content"): return r["content"][:500]
    except: pass

    return f"Komut işlendi: {komut[:100]}. Sistem yanıt bekliyor."


def _sistem_durumu() -> str:
    parts = []
    try:
        import requests
        r = requests.get("http://172.23.96.1:20128/api/health", timeout=2)
        parts.append("9router: AKTIF" if r.status_code == 200 else "9router: KAPALI")
    except: parts.append("9router: KAPALI")
    try:
        import torch
        if torch.cuda.is_available():
            parts.append(f"GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory//1024**2}MB)")
    except: pass
    try:
        import psutil
        parts.append(f"RAM: {psutil.virtual_memory().percent:.0f}%")
    except: pass
    return " | ".join(parts) if parts else "Sistem durumu alınamadı."


@app.get("/")
async def root():
    if FRONTEND.exists():
        return HTMLResponse(FRONTEND.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>NANO MATRIX — Frontend bulunamadı</h1>")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await mgr.connect(ws)
    await mgr.send(ws, {"type":"log","source":"sistem","message":"Nano Matris bağlantısı kuruldu."})
    await mgr.send(ws, {"type":"log","source":"sistem","message":_sistem_durumu()})

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                komut = msg.get("data", msg.get("command", ""))
            except:
                komut = data

            if not komut: continue
            await mgr.send(ws, {"type":"log","source":"komut","message":f"> {komut[:120]}"})

            # Arka planda işle
            loop = asyncio.get_event_loop()
            sonuc = await loop.run_in_executor(None, otonom_isle, komut)

            await mgr.send(ws, {"type":"response","data":sonuc[:500]})
            await mgr.send(ws, {"type":"log","source":"otonom","message":sonuc[:150]})

    except WebSocketDisconnect:
        await mgr.disconnect(ws)
    except Exception as e:
        await mgr.send(ws, {"type":"log","source":"hata","message":str(e)[:200]})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"NANO MATRIX Backend: ws://0.0.0.0:{port}/ws")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
