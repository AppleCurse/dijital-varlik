# 🗺️ dijital-varlik CANLI DURUM HARİTASI

**Tarih:** 2026-07-25
**Sistem:** Windows 10 IoT LTSC + WSL2 Ubuntu 24.04
**Amaç:** Neyin nerede olduğunu ve ne durumda olduğunu tek belgede toplamak

---

## 1. SİSTEM ÖZETİ

| Katman | Durum | Açıklama |
|--------|-------|----------|
| WSL2 | ✅ Ubuntu 24.04 Running | 2 WSL var: Ubuntu-24.04 (aktif), Ubuntu (stopped) |
| Docker | ❌ Çalışmıyor | docker ps başarısız |
| Tailscale | ✅ Çalışıyor | `trrdg2.taile8a0f0.ts.net` (Funnel açık) |
| Python | ⚠️ Windows Python | `/c/Users/Administrator/AppData/Local/Microsoft/WindowsApps/python3` |
| .venv | ⚠️ Mevcut mu? | `dijital-varlik/.venv/bin/python3` — kontrol edilemedi |

---

## 2. ÇALIŞAN / ÇALIŞMAYAN SERVİSLER

| Servis | Port | Durum | Not |
|--------|------|-------|-----|
| DeepSeek API | `api.deepseek.com` | ✅ 404 (normal — /models yok) | Claude proxy olarak kullanılıyor |
| 9router | `:20128` | ❌ Yanıt yok | `curl` timeout/bağlantı red |
| LiteLLM | `:4000` | ❓ Test edilemedi | WSL curl hatası |
| Browserless | `:3001` | ❓ Test edilemedi | Docker kapalı olabilir |
| OpenWebUI | `:3000` | ❓ | EC2'de çalıştığı varsayılıyor |
| Tailscale Funnel | `:443` | ✅ Açık | `trrdg2.taile8a0f0.ts.net` |

---

## 3. dijital-varlik PROJE YAPISI (GERÇEK)

### 3.1 Ana Python Dosyaları (kök dizin)

| Dosya | Satır | Rol | Durum |
|-------|-------|-----|-------|
| `agentik_dongu.py` | 939 | **Ana döngü** (Faz 8) | ⚠️ Aktif ama bridge duplikasyonları var |
| `zincir.py` | 370 | Zincir yürütme | ❓ |
| `bootstrap.py` | 307 | Başlangıç/setup | ❓ |
| `otonom.py` | 236 | Otonom mod | ❓ |
| `run.py` | 134 | Başlatıcı | ❓ |

⚠️ **Sorun:** `agentik_dongu.py` (939 satır) asıl dosya ama yanında 8+ test/destek dosyası var — hangisi ne zaman kullanılır belli değil:
- `test_izole.py`, `test_final.py`, `test_import.py`, `test_karar.py`, `test_altyapi.py`, `test_smol.py`, `test_mudahale.py`, `test_mahkeme_canli.py`, `final_test.py`, `teshis_hizli.py`, `check_models.py`

### 3.2 Katman 1 — Algı (`algi/`)

| Dosya | Boyut | Durum | Ne Yapar |
|-------|-------|-------|----------|
| `ses_odasi.py` | 16K | ❓ Standalone | FastAPI WebRTC ses sunucusu (:8081) |
| `algi_stt.py` | 3.9K | ❌ | sounddevice eksik, çalışmaz |
| `algi_tts.py` | 2.4K | ✅ | espeak-ng köprüsü, çalışıyor |

### 3.3 Katman 2 — Müdahale (`mudahale/`)

| Dosya | Boyut | Durum | Ne Yapar |
|-------|-------|-------|----------|
| `browser_use_bridge.py` | 8K | ✅ | Browserless CDP + browser-use Agent |
| `browser_bridge.py` | 3.5K | ❓ | Alternatif tarayıcı köprüsü? |
| `web_tools.py` | 3.7K | ✅ | 4 araç: fetch, title, screenshot, navigate |
| `openclaw_bridge.py` | 12K | ⚠️ | Kapsamlı ama agentik_dongu.py'de stub var |
| `voicebox_bridge.py` | 5.8K | ❓ | Ses kutusu entegrasyonu |
| `deepface_bridge.py` | 5.3K | ❓ | Yüz tanıma |
| `firecrawl_bridge.py` | 4K | ❓ | Web scraping alternatif |
| `weather_bridge.py` | 3.8K | ❓ | Hava durumu |
| `xtts_bridge.py` | ❓ | ❓ | XTTS metin-ses |
| `f5tts_bridge.py` | ❓ | ❓ | F5-TTS metin-ses |
| `qwen_bridge.py` | ❓ | ❓ | Qwen görüntü modeli |
| `pipecat_bridge.py` | ❓ | ❓ | Gerçek zamanlı ses |
| `atom_bridge.py` | ❓ | ❓ | A.T.O.M. asistan |
| `openhands_voicebox_bridge.py` | ❓ | ❓ | OpenHands ses |

### 3.4 Katman 3 — Karar (`karar/`)

| Dosya | Boyut | Durum | Ne Yapar |
|-------|-------|-------|----------|
| `mahkeme_engine.py` | 21K | ✅ | 4 rol: Savcı, Savunma, Şüpheci, Hakim |
| `harness.py` | 7.5K | ✅ | 6+ hata stratejisi |
| `smolagents_bridge.py` | 2.7K | ✅ | CodeAgent köprüsü |
| `aspasia.py` | 7.6K | ❓ | Ek karar mekanizması? |

### 3.5 Katman 4 — Altyapı (`altyapi/`)

| Dosya | Boyut | Durum | Ne Yapar |
|-------|-------|-------|----------|
| `mem0_bridge.py` | 8.9K | ⚠️ | Dosya fallback çalışıyor (DB locked) |
| `letta_bridge.py` | 4.2K | ⚠️ | Dosya fallback (EC2 Letta kapalı) |
| `litellm_bridge.py` | 4.2K | ❌ | 401 auth hatası |
| `ai_bridge.py` | 5.9K | ❓ | Genel AI köprüsü |
| `vram_manager.py` | 6.6K | ❓ | GPU VRAM yönetimi |
| `kesici.py` | ❓ | ❓ | ? |

### 3.6 Config (`config/`)

| Dosya | İçerik |
|-------|--------|
| `config.py` | Merkezi Python konfigürasyon |
| `.env` | 14 API anahtarı: LITELLM, MAHKEME, BROWSERLESS, MEM0, LETTA, TELEGRAM, FIRECRAWL, TAVILY, DEEPSEEK, GEMINI, GROQ, OPENROUTER |
| `litellm_config.yaml` | LiteLLM model routing |

### 3.7 Diğer Dizinler

| Dizin | İçerik |
|-------|--------|
| `voicebox/` | Ses sentezi backend (Flask, build_binary.py) |
| `runtime/` | Kernel, event bus, state manager, health check |
| `dashboard/` | Web dashboard (server.py) |
| `wsl_backend/` | WSL arka uç (FastAPI main.py) |
| `nodes/` | ? |
| `tools/` | ? |
| `docs/` | ? |
| `scripts/` | 18 script: test, deploy, watchdog, model kontrol... |

---

## 4. KLONLANMIŞ REPOLAR (ENVANTER.md'den)

17 repo klonlanmış, çoğu entegre değil:

| Repo | Durum | Gereksinim |
|------|-------|------------|
| BettaFish | ⚠️ İzole .venv yok | Sosyal medya istihbarat |
| F5-TTS | ❌ | GPU |
| Qwen2.5-VL | ❌ | GPU |
| Qwen3-VL | ❌ | GPU |
| AIRI | ❌ | WebGPU |
| A.T.O.M | ❌ | Modüler asistan |
| Pipecat | ❌ | GPU |
| Skyvern | ⚠️ | Otonom web |
| Letta | ⚠️ | EC2'de, lokal fallback |
| Mem0 | ⚠️ | DB locked |
| Hebo Gateway | ❓ | LLM routing |
| Harness SDK | ✅ | Zaten lokal kodda |
| Heretic | ❓ | TTS alternatif? |
| Open WebUI | ❓ | EC2'de olabilir |
| Code Server | ❓ | VS Code web |
| Browserless | ✅ (Docker?) | Şu an çalışmıyor |
| smolagents | ✅ | Zaten pip'te |
| OpenClaw | ✅ | Klonlanmış, bridge hazır |

Eksik: `agent-reach`

---

## 5. TÜM AJAN / ARAÇ KONFİGÜRASYONLARI (ev dizini)

### 5.1 ÖZET TABLO

| # | Dizin | Ne | Aktif mi? | Model/Provider | API Key |
|---|-------|-----|-----------|----------------|---------|
| 1 | `.claude/` | Claude Code | ✅ **AKTİF** | deepseek-v4-pro | `sk-b0323...` |
| 2 | `.codewhale/` | CodeWhale AI IDE | ❓ | deepseek-v4-pro | `sk-58bbad...` |
| 3 | `.gemini/` | Google Gemini CLI | ❓ | Gemini API key | GEMINI_API_KEY |
| 4 | `.openhands/` | OpenHands (All Hands AI) | ❓ | deepseek-v4-flash | Memory'de saklı |
| 5 | `.openinterpreter/` | Open Interpreter | ❓ | gpt-5.5, gpt-5.6-sol | ❓ |
| 6 | `.omniroute/` | LLM yönlendirici | ❌ Offline (62 gün) | — | server.env |
| 7 | `.9router/` | 9router LLM gateway | ❌ Yanıt vermiyor | deepseek-v4-pro | JWT secret mevcut |
| 8 | `.deepdive/` | DeepDive araştırma | ❓ | DeepSeek | `sk-6a27c6...` |
| 9 | `.deepseek/` | DeepSeek CLI | ❓ | — | — |
| 10 | `.orb-cli/` | Orb CLI | ❓ | claude-3-sonnet | Kendi key'i var |
| 11 | `.insightface/` | Yüz tanıma modeli | ❓ | — | — |
| 12 | `.landscape/` | Sistem izleme | ❓ | — | — |
| 13 | `.mem0/` | Mem0 bellek | ⚠️ DB locked | — | — |

### 5.2 Detaylar

#### ✅ `.claude/` — Claude Code (AKTİF KULLANILIYOR)
```
Provider: DeepSeek API (api.deepseek.com/anthropic)
Model: deepseek-v4-pro (ana), deepseek-v4-flash (subagent)
Auth: ***GİZLİ_API_ANAHTARI*** (settings.json)
Effort: max
```
**Şu an bununla konuşuyorsunuz.** Çalışan tek şey bu.

#### ❓ `.codewhale/` — CodeWhale
```
Provider: OpenAI-compatible
URL: http://127.0.0.1:20128/v1 → 9router üzerinden!
Model: ds/deepseek-v4-pro
Auth: sk-58bbadde44171bff-6jq5bl-7378c3af
```
⚠️ 9router çalışmadığı için bu da çalışmaz.

#### ❓ `.openhands/` — OpenHands
```
Model: deepseek/deepseek-v4-flash
Özellik: SWE-bench agent, terminal + file editor + task tracker
Auth: agent_settings.json içinde (Memory Condensation ile karışmış!)
```
⚠️ API key alanına yanlışlıkla Memory Condensation dökümantasyonu yazılmış!

#### ❌ `.omniroute/` — OmniRoute
```
Durum: 62 gündür offline (tailscale status)
Dosya: server.env (ayrı config)
```

#### ❌ `.9router/` — 9router
```
Tailscale: trrdg2.taile8a0f0.ts.net (Funnel açık)
Curl test: Yanıt yok (401 auth veya servis kapalı)
JWT: Mevcut
Auth: cli-secret dosyası var
```
**Kritik:** Bu çalışmayınca LiteLLM, CodeWhale, ve tüm LLM zinciri kopuyor.

---

## 6. API ANAHTARI ENVANTERİ

| Servis | Key Konumu | Key ID (maskeli) |
|--------|-----------|-------------------|
| **DeepSeek (Claude Code)** | `.claude/settings.json` | `sk-b0323a6ec2254...` |
| **DeepSeek (DeepDive)** | `.deepdive/settings.json` | `sk-6a27c6fe55ba...` |
| **9router (CodeWhale)** | `.codewhale/config.toml` | `sk-58bbadde4417...` |
| **9router (LiteLLM)** | `dijital-varlik/config/.env` | `sk-5762d1405ced...` |
| **OpenHands** | `.openhands/agent_settings.json` | Memory'de saklı (karışık!) |
| **Orb CLI** | `.orb-cli/config.json` | Uzun key, ayrı servis |
| **Gemini** | `.gemini/` veya `.env` | GEMINI_API_KEY |
| **Telegram** | `dijital-varlik/config/.env` | TELEGRAM_BOT_TOKEN |
| **Firecrawl** | `dijital-varlik/config/.env` | FIRECRAWL_API_KEY |
| **Tavily** | `dijital-varlik/config/.env` | TAVILY_API_KEY |
| **Groq** | `dijital-varlik/config/.env` | GROQ_API_KEY |
| **OpenRouter** | `dijital-varlik/config/.env` | OPENROUTER_API_KEY |

⚠️ **Toplam 12 API key** farklı yerlerde dağılmış durumda.

---

## 7. SORUN ENVANTERİ

### 🔴 Kritik (çalışmayı engelliyor)

| # | Sorun | Etki | Çözüm |
|---|-------|------|-------|
| 1 | **9router yanıt vermiyor** | LiteLLM → LLM çağrıları yapılamaz | 9router'ı başlat veya direkt DeepSeek API'ye geç |
| 2 | **LiteLLM 401 auth** | Mahkeme, smolagents, browser-use çalışmaz | 9router çalışırsa düzelir |
| 3 | **Docker çalışmıyor** | Browserless, OpenWebUI, diğer container'lar kapalı | `sudo service docker start` |

### 🟡 Yapısal (karışıklık yaratıyor)

| # | Sorun | Detay |
|---|-------|-------|
| 4 | **Çift ana dosya** | `agentik_dongu.py` (939 satır) vs `orchestrator.py` — ikincisi deprecated |
| 5 | **Çift mahkeme** | `karar/mahkeme_engine.py` (canonical) vs `mahkeme/mahkeme_engine.py` (eski) |
| 6 | **Bridge duplikasyonları** | OpenClaw, AgentReach: hem agentik_dongu.py içinde stub hem ayrı dosya |
| 7 | **Çift ses mimarisi** | `ses_odasi.py` (WebRTC standalone) vs `algi_stt.py/algi_tts.py` (direkt) |
| 8 | **14 test/yardımcı .py** | Kök dizinde hangisi ne zaman kullanılır belli değil |
| 9 | **17 repo klonlanmış** | Çoğu GPU bekliyor, entegre değil |
| 10 | **OpenHands config bozuk** | API key alanına dökümantasyon metni yazılmış |
| 11 | **12 API key 7 farklı yerde** | Merkezi yönetim yok |

### 🟢 Çalışan / Sağlam

| # | Bileşen | Durum |
|---|--------|-------|
| 1 | Claude Code (DeepSeek proxy) | ✅ Şu an kullanılıyor |
| 2 | Tailscale + Funnel | ✅ `trrdg2.taile8a0f0.ts.net` |
| 3 | Mahkeme motoru (kod) | ✅ 4 rol, claim/task modu |
| 4 | Harness (kod) | ✅ 6+ hata stratejisi |
| 5 | smolagents bridge (kod) | ✅ CodeAgent |
| 6 | browser-use bridge (kod) | ✅ Browserless CDP |
| 7 | TTS (espeak) | ✅ Çalışıyor |
| 8 | Mem0 (dosya fallback) | ⚠️ Yavaş ama çalışıyor |

---

## 8. MİMARİ AKIŞ (Kağıt Üstünde)

```
Kullanıcı
    │
    ▼
Claude Code (.claude/)          ← ✅ Şu an TEK çalışan
    │  deepseek-v4-pro
    │
    ▼
agentik_dongu.py (939 satır)    ← ⚠️ Ana dosya
    │
    ├─ Mahkeme (karar/)          ← ✅ Kod OK, LLM auth ❌
    ├─ smolagents (karar/)       ← ✅ Kod OK, LLM auth ❌
    ├─ browser-use (mudahale/)   ← ✅ Kod OK, LLM auth ❌
    ├─ Harness (karar/)          ← ✅ Bağımsız çalışır
    ├─ Mem0 (altyapi/)           ← ⚠️ Dosya fallback
    ├─ Letta (altyapi/)          ← ⚠️ Dosya fallback
    ├─ LiteLLM (altyapi/)        ← ❌ Auth hatası
    └─ TTS (algi/)               ← ✅ espeak
```

**Gerçek:** Zincirin sadece ilk halkası (Claude Code) ve kod kısmı sağlam. LLM bağımlı tüm halkalar kopuk.

---

## 9. HIZLI DÜZELTME YOL HARİTASI

### Adım 1: LLM'i düzelt (en kritik)
```bash
# Seçenek A: 9router'ı başlatmayı dene
cd ~/.9router && ./bin/9router start

# Seçenek B: agentik_dongu.py'yi direkt DeepSeek API'ye yönlendir
# litellm_bridge.py'de base_url = "https://api.deepseek.com/anthropic" yap
```

### Adım 2: Docker'ı başlat
```bash
sudo service docker start
docker start browserless open-webui  # container isimlerini kontrol et
```

### Adım 3: Temizlik
```bash
# Eski dosyaları arşivle
mkdir -p dijital-varlik/archive
mv dijital-varlik/orchestrator.py dijital-varlik/archive/   # deprecated
mv dijital-varlik/mahkeme dijital-varlik/archive/           # eski mahkeme
mv dijital-varlik/*.bak dijital-varlik/archive/             # yedekler
mv dijital-varlik/*.bozuk dijital-varlik/archive/           # bozuklar
```

### Adım 4: Config'leri birleştir
Tüm API key'leri tek `.env` altında topla, 7 farklı yerde dağıtma.

---

## 10. SON SÖZ

**Kağıt üstünde:** 4 katmanlı, 17 repolu, Hakikat Mahkemesi filtreli devasa bir siber organizma.

**Gerçekte:** Claude Code (DS proxy) çalışıyor, Tailscale çalışıyor, kod altyapısı hazır ama LLM bağlantısı koptuğu için zincirin %90'ı test edilemiyor. 12 ajan/araç konfigürasyonu ev dizininde dağınık, hangisinin aktif olduğu belli değil.

**Öneri:** Önce `HARITA.md`'yi oku, sonra Adım 1'den başlayarak düzeltmeye geç.
