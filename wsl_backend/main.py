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
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

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


def otonom_isle(komut: str) -> dict:
    """Komutu işle, {type, data, source} döndür."""
    k = komut.lower().strip()

    # ── DURUM ──
    if k in ("durum", "status", "sistem"):
        return {"type": "status", "data": _sistem_durumu(), "source": "sistem"}

    # ── BASİT CEVAPLAR ──
    basit = {
        "saat": lambda: f"Saat: {datetime.now().strftime('%H:%M:%S')}",
        "tarih": lambda: f"Tarih: {datetime.now().strftime('%d.%m.%Y')}",
        "merhaba": lambda: "Merhaba Mösyö. Dijital Varlık Nano Matris emrinizde.",
        "nasılsın": lambda: "Tüm sistemler nominal. Mahkeme aktif, Kesici tetikte.",
        "kimsin": lambda: "Dijital Varlık — otonom AI organizması. 4 Mahkeme rolü, 6 zincir, 75 model.",
        "yardım": lambda: "KOMUTLAR: saat, tarih, ara [konu], kod [görev], web [url], yüz [foto], ekran, durum",
        "selam": lambda: "Selam Mösyö. Nano Matris bağlantısı stabil.",
    }
    for anahtar, fn in basit.items():
        if k == anahtar or k.startswith(anahtar):
            return {"type": "response", "data": fn(), "source": "kesici"}

    # ── KESİCİ ──
    try:
        from altyapi.kesici import kesici
        local = kesici.tani(komut)
        if local: return {"type": "response", "data": local, "source": "kesici"}
    except: pass

    # ── KOD ──
    if any(kw in k for kw in ["kod", "python", "script", "hesapla", "topla", "yaz"]):
        return _zincir("kod", komut)

    # ── WEB ──
    if any(kw in k for kw in ["site", "web", "http", "başlık", "example", "gez", "tıkla"]):
        return _zincir("web", komut)

    # ── GÖRÜ ──
    if any(kw in k for kw in ["ekran", "görüntü", "grafik", "analiz et"]):
        return _zincir("goru", komut)

    # ── YÜZ ──
    if any(kw in k for kw in ["yüz", "fotoğraf", "resim", "tanı"]):
        return {"type": "response", "data": "Yüz tanıma için dashboard'dan fotoğraf yükleyin: http://localhost:9998", "source": "sistem"}

    # ── ARAMA / BİLGİ ──
    if any(kw in k for kw in ["ara", "nedir", "kimdir", "araştır", "wikipedia"]):
        try:
            from mudahale.atom_bridge import get_atom
            atom = get_atom()
            r = atom.web_arama(komut)
            if r.get("status") == "ok":
                return {"type": "response", "data": str(r.get("sonuc",""))[:500], "source": "atom"}
        except: pass

    # ── LLM (9Router) ──
    try:
        from altyapi.litellm_bridge import litellm
        r = litellm.chat([{"role":"user","content":komut}], max_tokens=300)
        if r and r.get("content"):
            return {"type": "response", "data": r["content"][:500], "source": r.get("model","llm")}
    except: pass

    return {"type": "response", "data": f"Komut alındı: {komut[:100]}", "source": "sistem"}


def _zincir(tip: str, komut: str) -> dict:
    """Zincirleri subprocess ile çalıştır."""
    try:
        from zincir import zincir_kod, zincir_ses, zincir_goru
        if tip == "kod":
            r = zincir_kod(komut)
        elif tip == "web":
            r = zincir_ses(komut)
        elif tip == "goru":
            r = zincir_goru()
        else:
            r = zincir_ses(komut)

        msg = str(r)[:500] if isinstance(r, str) else str(r.get("message",""))[:500]
        return {"type": "response", "data": msg or "Tamamlandı", "source": tip}
    except Exception as e:
        return {"type": "response", "data": f"Hata: {str(e)[:200]}", "source": "hata"}


def _sistem_durumu() -> str:
    parts = []
    try:
        import requests
        r = requests.get("http://172.23.96.1:20128/api/health", timeout=2)
        parts.append("9router: AKTIF" if r.status_code == 200 else "9router: KAPALI")
    except: parts.append("9router: KAPALI")
    try:
        import requests
        r = requests.get("http://localhost:3004/json/version", timeout=2)
        parts.append("Browser: AKTIF" if r.status_code == 200 else "Browser: KAPALI")
    except: parts.append("Browser: KAPALI")
    try:
        import torch
        if torch.cuda.is_available():
            parts.append(f"GPU: {torch.cuda.get_device_name(0).replace('NVIDIA ','')} ({torch.cuda.get_device_properties(0).total_memory//1024**2}MB)")
    except: pass
    try:
        import psutil
        parts.append(f"RAM: {psutil.virtual_memory().percent:.0f}%")
    except: pass
    try:
        from mudahale.deepface_bridge import get_deepface
        parts.append(f"DeepFace: {'AKTIF' if get_deepface().hazir_mi() else 'YOK'}")
    except: parts.append("DeepFace: YOK")
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
    await mgr.send(ws, {"type":"status","data":_sistem_durumu(),"source":"sistem"})
    await mgr.send(ws, {"type":"capabilities","data":{
        "sohbet": True, "kod": True, "web": True, "goru": True,
        "yuz": True, "arama": True, "ses": True, "hafiza": True
    }})

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

            await mgr.send(ws, sonuc)
            await mgr.send(ws, {"type":"log","source":sonuc.get("source","?"),
                               "message":str(sonuc.get("data",""))[:150]})

    except WebSocketDisconnect:
        await mgr.disconnect(ws)
    except Exception as e:
        await mgr.send(ws, {"type":"log","source":"hata","message":str(e)[:200]})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"NANO MATRIX Backend: ws://0.0.0.0:{port}/ws")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
