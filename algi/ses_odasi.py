"""
╔══════════════════════════════════════════════════════════╗
║  SES ODASI — WebRTC Canli Ses Sunucusu                  ║
║  Mikrofon → Whisper STT → LLM → espeak TTS → Hoparlor  ║
║  Port: 8081                                             ║
╚══════════════════════════════════════════════════════════╝
"""
import asyncio
import json
import base64
import io
import wave
import struct
import time
import sys
import threading
import numpy as np
from pathlib import Path
from datetime import datetime

# Proje yolu
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
import uvicorn

# Gercek STT/TTS motorlari
from algi.algi_stt import GercekMikrofon
from algi.algi_tts import GercekTTS

# LLM (LiteLLM uzerinden)
from altyapi.litellm_bridge import litellm

app = FastAPI(title="Ses Odası", version="1.0")

# Motorlar
stt_engine = GercekMikrofon(model_boyutu="tiny")
tts_engine = GercekTTS()
aktif_oturumlar = {}
tts_konusuyor = threading.Lock()  # TTS sirasinda STT'yi sustur
islenmis_metinler = set()  # Ayni metni tekrar tekrar isleme

# ================================================================
# HTML ARAYUZU — WebRTC Ses Yakalama
# ================================================================

SES_ODASI_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎙 Ses Odasi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#e0e0e0;font-family:system-ui;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh}
.container{width:90%;max-width:600px;padding:20px}
h1{text-align:center;color:#00ff88;margin-bottom:20px;font-size:1.8em}
.status{background:#1a1a1a;border-radius:12px;padding:20px;margin:10px 0}
.status.active{box-shadow:0 0 20px #00ff8844}
.row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #222}
.row:last-child{border:none}
.label{color:#888;font-size:0.9em}
.value{font-weight:bold}
.value.on{color:#00ff88}
.value.off{color:#ff4444}
.btn{display:block;width:100%;padding:18px;margin:15px 0;border:none;border-radius:12px;font-size:1.2em;font-weight:bold;cursor:pointer;transition:all 0.3s}
.btn.start{background:#00ff88;color:#000}
.btn.start:hover{background:#00cc6a;transform:scale(1.02)}
.btn.stop{background:#ff4444;color:#fff}
.btn.stop:hover{background:#cc3333}
.btn:disabled{opacity:0.4;cursor:not-allowed}
.log{background:#111;border-radius:8px;padding:12px;height:200px;overflow-y:auto;font-family:monospace;font-size:0.85em;margin-top:10px}
.log div{padding:3px 0}
.log .stt{color:#00ff88}
.log .tts{color:#ffaa00}
.log .info{color:#888}
.pulse{animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
</style>
</head>
<body>
<div class="container">
<h1>🎙 Ses Odasi</h1>
<div class="status" id="statusBox">
<div class="row"><span class="label">STT (Kulak)</span><span class="value off" id="sttStatus">bekliyor</span></div>
<div class="row"><span class="label">TTS (Agiz)</span><span class="value off" id="ttsStatus">bekliyor</span></div>
<div class="row"><span class="label">Oturum</span><span class="value" id="sessionId">—</span></div>
</div>
<button class="btn start" id="startBtn" onclick="startSession()">▶ BASLAT — Mikrofonu Ac</button>
<button class="btn stop" id="stopBtn" onclick="stopSession()" disabled>⏹ DURDUR</button>
<div class="log" id="log"></div>
</div>
<script>
let ws = null;
let mediaStream = null;
let audioContext = null;
let sessionId = null;

function log(msg, cls='info') {
    const d = document.getElementById('log');
    const div = document.createElement('div');
    div.className = cls;
    div.textContent = new Date().toLocaleTimeString() + ' ' + msg;
    d.appendChild(div);
    d.scrollTop = d.scrollHeight;
}

async function startSession() {
    try {
        document.getElementById('startBtn').disabled = true;
        log('Mikrofon izni isteniyor...', 'info');

        // Mikrofon stream'i al
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(mediaStream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);

        // WebSocket baglantisi
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(protocol + '//' + location.host + '/ws/ses');

        ws.onopen = () => {
            log('🟢 Ses odasina baglanildi', 'info');
            document.getElementById('statusBox').classList.add('active');
            document.getElementById('stopBtn').disabled = false;
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'session') {
                sessionId = data.id;
                document.getElementById('sessionId').textContent = sessionId.slice(0,8);
            } else if (data.type === 'stt') {
                log('🎤 SEN: ' + data.text, 'stt');
                document.getElementById('sttStatus').textContent = 'dinliyor';
                document.getElementById('sttStatus').className = 'value on pulse';
            } else if (data.type === 'tts') {
                log('🤖 AI: ' + data.text, 'tts');
                document.getElementById('ttsStatus').textContent = 'konusuyor';
                document.getElementById('ttsStatus').className = 'value on pulse';
                // TTS sesini cal
                playTTSAudio(data.audio);
            } else if (data.type === 'status') {
                document.getElementById('sttStatus').textContent = data.stt;
                document.getElementById('sttStatus').className = 'value ' + (data.stt === 'hazir' ? 'on' : 'off');
                document.getElementById('ttsStatus').textContent = data.tts;
                document.getElementById('ttsStatus').className = 'value ' + (data.tts === 'hazir' ? 'on' : 'off');
            }
        };

        ws.onclose = () => { log('Baglanti kapandi', 'info'); stopSession(); };
        ws.onerror = (e) => { log('Baglanti hatasi', 'info'); };

        // Ses verisini gonder
        let buffer = [];
        let silenceCount = 0;
        processor.onaudioprocess = (e) => {
            if (!ws || ws.readyState !== WebSocket.OPEN) return;
            const input = e.inputBuffer.getChannelData(0);
            buffer.push(...Array.from(input));

            // Her 0.5 saniyede bir gonder
            if (buffer.length >= 8000) {
                const rms = Math.sqrt(buffer.reduce((s,v)=>s+v*v,0)/buffer.length);
                if (rms > 0.005) {
                    silenceCount = 0;
                    const int16 = new Int16Array(buffer.length);
                    for (let i = 0; i < buffer.length; i++) {
                        int16[i] = Math.max(-32768, Math.min(32767, buffer[i] * 32768));
                    }
                    ws.send(int16.buffer);
                } else {
                    silenceCount++;
                    if (silenceCount > 5 && buffer.length > 16000) {
                        // Sessizlik — buffer'i gonder ve temizle
                        const int16 = new Int16Array(buffer.length);
                        for (let i = 0; i < buffer.length; i++) {
                            int16[i] = Math.max(-32768, Math.min(32767, buffer[i] * 32768));
                        }
                        ws.send(int16.buffer);
                        buffer = [];
                        silenceCount = 0;
                    }
                }
                buffer = buffer.slice(-4000); // son 0.25s'yi tut
            }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);

    } catch (err) {
        log('HATA: ' + err.message, 'info');
        document.getElementById('startBtn').disabled = false;
    }
}

function playTTSAudio(base64wav) {
    try {
        const binary = atob(base64wav);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
        audio.onended = () => URL.revokeObjectURL(url);
    } catch(e) { console.error('TTS playback error:', e); }
}

function stopSession() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(t => t.stop());
        mediaStream = null;
    }
    if (audioContext) { audioContext.close(); audioContext = null; }
    if (ws) { ws.close(); ws = null; }
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('statusBox').classList.remove('active');
    document.getElementById('sttStatus').textContent = 'bekliyor';
    document.getElementById('sttStatus').className = 'value off';
    document.getElementById('ttsStatus').textContent = 'bekliyor';
    document.getElementById('ttsStatus').className = 'value off';
    log('Oturum sonlandi', 'info');
}
</script>
</body>
</html>"""

# ================================================================
# API ENDPOINTS
# ================================================================

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    return HTMLResponse(content=SES_ODASI_HTML)


@app.websocket("/ws/ses")
async def ses_websocket(ws: WebSocket):
    await ws.accept()
    oturum_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(id(ws))[-6:]
    aktif_oturumlar[oturum_id] = {"ws": ws, "baslangic": time.time()}

    # Oturum bilgisi gonder
    await ws.send_json({
        "type": "session",
        "id": oturum_id,
        "stt": "hazir" if stt_engine.hazir_mi() else "yok",
        "tts": "hazir" if tts_engine.hazir_mi() else "yok",
    })
    await ws.send_json({
        "type": "status",
        "stt": "hazir" if stt_engine.hazir_mi() else "yok",
        "tts": "hazir" if tts_engine.hazir_mi() else "yok",
    })

    print(f"[SES ODASI] Yeni baglanti: {oturum_id}")

    ses_buffer = bytearray()
    son_islem_zamani = 0.0  # flood onleme

    try:
        while True:
            data = await ws.receive()

            if data["type"] == "websocket.receive":
                if "bytes" in data:
                    # TTS konusuyorsa mikrofonu yok say (yanki onleme)
                    if tts_konusuyor.locked():
                        continue

                    ses_buffer.extend(data["bytes"])

                    # 0.8 saniyelik ses birikince isle
                    if len(ses_buffer) >= 25600:
                        raw = bytes(ses_buffer[:25600])
                        ses_buffer = ses_buffer[25600:]

                        # Flood onleme: son islemden < 2s gectiyse atla
                        simdi = time.time()
                        if simdi - son_islem_zamani < 2.0:
                            continue

                        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

                        # RMS esik kontrolu — sadece gercek insan sesi
                        rms = float(np.sqrt(np.mean(samples ** 2)))
                        if rms < 0.008:
                            continue

                        # STT — TURKCE
                        if stt_engine.hazir_mi():
                            metin = stt_engine.sesi_metne_cevir(samples)
                            if metin and len(metin) > 1 and metin not in islenmis_metinler:
                                islenmis_metinler.add(metin)
                                son_islem_zamani = simdi
                                print(f"[SES] STT: {metin}")
                                await ws.send_json({"type": "stt", "text": metin})

                                # MIKROFONU SUSTUR, TTS baslasin
                                with tts_konusuyor:
                                    # LLM
                                    cevap = litellm.chat(
                                        [{"role": "user", "content": metin}],
                                        model="deepseek-v4-flash",
                                        max_tokens=256
                                    )
                                    if cevap and cevap.get("content"):
                                        ai_metin = cevap["content"].strip()
                                        print(f"[SES] AI: {ai_metin}")
                                        await ws.send_json({"type": "tts", "text": ai_metin[:80]})

                                        # TTS → WAV
                                        if tts_engine.hazir_mi():
                                            import tempfile
                                            wav_path = tempfile.mktemp(suffix=".wav")
                                            saved = tts_engine.dosyaya_kaydet(ai_metin, wav_path)
                                            if saved:
                                                with open(saved, "rb") as f:
                                                    audio_b64 = base64.b64encode(f.read()).decode()
                                                await ws.send_json({
                                                    "type": "tts",
                                                    "text": ai_metin[:80],
                                                    "audio": audio_b64
                                                })
                                                Path(saved).unlink(missing_ok=True)

                                # TTS bitince mikrofon otomatik acilir (lock release)

                elif "text" in data:
                    try:
                        msg = json.loads(data["text"])
                        if msg.get("action") == "ping":
                            await ws.send_json({"type": "pong"})
                    except:
                        pass

            elif data["type"] == "websocket.disconnect":
                break

    except Exception as e:
        print(f"[SES ODASI] Hata ({oturum_id}): {e}")
    finally:
        del aktif_oturumlar[oturum_id]
        print(f"[SES ODASI] Baglanti koptu: {oturum_id}")


# ================================================================
# BASLAT
# ================================================================

def baslat(host: str = "0.0.0.0", port: int = 8081):
    print("╔════════════════════════════════════╗")
    print("║  🎙 SES ODASI — WebRTC Sunucusu  ║")
    print("╠════════════════════════════════════╣")
    print(f"║  Adres : http://{host}:{port}             ║")
    print(f"║  STT   : {'✅ faster-whisper' if stt_engine.hazir_mi() else '❌'}      ║")
    print(f"║  TTS   : {'✅ espeak-ng' if tts_engine.hazir_mi() else '❌'}        ║")
    print(f"║  LLM   : ✅ LiteLLM:4000          ║")
    print("╚════════════════════════════════════╝")
    print("\n🎤 Tarayicidan http://localhost:8081 ac, BASLAT'a tikla.")
    print("   Mikrofon → Whisper → LLM → espeak → Kulaklik\n")

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    baslat()
