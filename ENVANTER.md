# DIJITAL-VARLIK — TAM ENVANTER
**Tarih:** 2026-07-04
**Ana Dosya:** agentik_dongu.py (821 satır)

---

## 🟢 ÇALIŞAN SİSTEMLER

### Lokal Servisler
| Servis | Port | Durum | Not |
|--------|------|-------|-----|
| Browserless | 3001 | ✅ ÇALIŞIYOR | HeadlessChrome/121.0.6167.85 |
| LiteLLM | 4000 | ❌ AUTH HATASI | "No api key passed in" |

**LiteLLM Config:**
- URL: `http://localhost:4000`
- Key: `sk-5762d1405cedb9c7-txz14a-1ae81231`
- 9router URL: `http://trrdg2.taile8a0f0.ts.net:20128/v1` (401 auth hatası)
- Model: `kr/claude-sonnet-4.5`

### Python Paketleri (pip)
```
browser-use        0.13.2  ✅
browser-use-sdk    3.4.2   ✅
mem0ai             2.0.10  ⚠️  (DB locked, dosya fallback)
smolagents         1.26.0  ✅
litellm            1.90.0  ✅ (kurulu ama auth hatası)
```

**Eksik pip paketleri:**
- `sounddevice` (STT için gerekli)
- `faster-whisper` (STT için gerekli)
- `pipecat` (gerçek zamanlı ses için)

---

## 🟡 LOKAL IMPLEMENTASYONLAR (Çalışan)

### Katman 3 - Karar (karar/)
| Dosya | Boyut | Durum | İçerik |
|-------|-------|-------|--------|
| mahkeme_engine.py | 14K | ✅ | 4 rol (Savcı, Savunma, Şüpheci, Hakim) |
| harness.py | 5.4K | ✅ | 7 hata stratejisi |
| smolagents_bridge.py | 2.7K | ✅ | CodeAgent köprüsü |

### Katman 4 - Altyapı (altyapi/)
| Dosya | Boyut | Durum | İçerik |
|-------|-------|-------|--------|
| mem0_bridge.py | 8.9K | ⚠️ | Dosya fallback çalışıyor |
| letta_bridge.py | 4.2K | ✅ | Oturum yönetimi |
| litellm_bridge.py | 3.5K | ❌ | Auth hatası |

### Katman 2 - Müdahale (mudahale/)
| Dosya | Boyut | Durum | İçerik |
|-------|-------|-------|--------|
| browser_use_bridge.py | 7.4K | ✅ | Browserless CDP entegrasyonu |
| web_tools.py | 3.7K | ✅ | 4 araç (fetch, title, screenshot, navigate) |
| bettafish_bridge.py | 13K | ❌ | .venv_betta yok |
| skyvern_bridge.py | 2.6K | ❌ | Entegre değil |
| browser_bridge.py | 3.5K | ❓ | Kullanılmıyor? |

### Katman 1 - Algı (algi/)
| Dosya | Boyut | Durum | İçerik |
|-------|-------|-------|--------|
| ses_odasi.py | 16K | ❓ | FastAPI WebRTC sunucu (standalone, entegre değil) |
| algi_tts.py | 2.4K | ✅ | espeak-ng köprüsü |
| algi_stt.py | 3.9K | ❌ | sounddevice eksik |

---

## 🔴 KLONLANMIŞ AMA ENTEGRE DEĞİL

### Hazır Repolar (klonlanmış, kurulum bekliyor)
```
✅ BettaFish-main/          → Sosyal medya istihbarat (izole .venv gerekli)
✅ F5-TTS-main/             → Ses klonlama (GPU gerekli)
✅ Qwen2.5-VL-main/         → Görme modeli (GPU gerekli)
✅ Qwen3-VL-main/           → Görme modeli v3 (GPU gerekli)
✅ airi-main/               → 3D Avatar (WebGPU)
✅ atom-main/               → Modüler asistan OS
✅ pipecat-main/            → Gerçek zamanlı ses (GPU gerekli)
✅ skyvern-main/            → Otonom web (entegre edilecek)
✅ letta-main/              → Hafıza (zaten lokal bridge var)
✅ mem0-main/               → Hafıza (zaten pip kurulu)
✅ hebo-gateway-main/       → LLM routing
✅ harness-sdk-main-outer/  → Hata yönetimi (zaten lokal var)
✅ heretic-master/          → TTS alternatif?
✅ open-webui-main/         → Kokpit UI
✅ code-server-main/        → VS Code web
✅ browserless-main/        → Headless browser (zaten çalışıyor)
✅ smolagents-main/         → Code agents (zaten pip kurulu)
```

### Eksik Repolar (klonlanacak)
```
❌ openclaw              → WhatsApp/Telegram mesajlaşma
❌ agent-reach           → Sosyal medya istihbarat (Reddit, Twitter, TikTok)
```

---

## ⚙️ agentik_dongu.py ENTEGRASYON DURUMU

### Built-in (agentik_dongu.py içinde tanımlı)
```python
✅ AgentSBridge          → Windows TCP :9999 kontrolü (sunucu çalışmıyor)
⚠️  OpenClawBridge       → Stub (mudahale/openclaw_bridge.py silinmiş)
⚠️  AgentReachBridge     → Stub (mudahale/agentreach_bridge.py silinmiş)
```

### Import Edilen
```python
✅ HakikatMahkemesi      → karar/mahkeme_engine.py
✅ get_harness()         → karar/harness.py
✅ get_mem0()            → altyapi/mem0_bridge.py
✅ get_letta()           → altyapi/letta_bridge.py
✅ litellm               → altyapi/litellm_bridge.py
✅ get_browser_use()     → mudahale/browser_use_bridge.py
✅ get_smol()            → karar/smolagents_bridge.py
✅ web_tools (4 adet)    → mudahale/web_tools.py
⚠️  BettaFishBridge      → mudahale/bettafish_bridge.py (conditional, devre dışı)
✅ _get_tts()            → algi/algi_tts.py
❌ get_mikrofon()        → algi/algi_stt.py (sounddevice eksik)
```

---

## 🚫 KRİTİK BLOKERLAR

### 1. LiteLLM Auth (EN ÖNEMLİ)
**Sorun:** Tüm LLM çağrıları 401 hatası veriyor
**Etki:** Mahkeme, smolagents, browser-use çalışamıyor
**Config:**
- LiteLLM URL: `http://localhost:4000`
- 9router URL: `http://trrdg2.taile8a0f0.ts.net:20128/v1`
- Key: `.env` dosyasında mevcut

**Aksiyon:** LiteLLM/9router API key doğrulaması gerekli

### 2. Mem0 Database Lock
**Sorun:** SQLite DB locked
**Geçici Çözüm:** Dosya tabanlı fallback çalışıyor
**Aksiyon:** DB lock'u çözülmeli

### 3. GPU Eksik
**Etki:** Qwen3-VL, F5-TTS, Pipecat çalışamaz
**Aksiyon:** GPU sürücü kurulumu / bulut GPU

### 4. sounddevice Eksik
**Etki:** Mikrofon girişi yok
**Aksiyon:** `pip install sounddevice`

### 5. Agent S Sunucu
**Sorun:** Windows PowerShell sunucu çalışmıyor
**Aksiyon:** `powershell -File agent_s_server.ps1`

---

## 📊 ÖZET

**Sistem Durumu:** %65 hazır, ama LLM auth hatası nedeniyle test edilemiyor

**Çalışan Bileşenler (8):**
1. Mahkeme motoru (kod OK, LLM auth hatası)
2. Harness (7 strateji)
3. smolagents (kod OK, LLM auth hatası)
4. browser-use (kod OK, LLM auth hatası)
5. Browserless :3001 ✅
6. Letta
7. TTS (espeak) ✅
8. Mem0 (dosya fallback)

**Bekleyen Bileşenler (5):**
1. LiteLLM auth düzeltmesi (ENGELLEYİCİ)
2. BettaFish kurulumu
3. Skyvern entegrasyonu
4. STT kurulumu
5. Agent S sunucu başlatma

**Eksik Entegrasyonlar:**
- OpenClaw, Agent-Reach (repolar klonlanacak)
- GPU gerektiren: Qwen3-VL, F5-TTS, Pipecat, AIRI

**SONRAKİ ADIM:** LiteLLM API key sorununu çöz, aksi halde hiçbir LLM çağrısı yapılamaz.
