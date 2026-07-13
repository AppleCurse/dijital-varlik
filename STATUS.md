# dijital-varlık — Proje Durumu (STATUS.md)

> Son güncelleme: 2026-07-04 12:42
> Faz: 8 — Ana dosya: agentik_dongu.py (821 satır)
> Temizlik: orchestrator.py (deprecated), mahkeme/ (duplicate), bridge duplikasyonları silindi

---

## Faz 1: Çekirdek Döngü ✅

### K1: Uçtan Uca Görev Çalıştırma ✅

**Test:** `https://example.com sitesini ac ve sayfa basligini soyle`

| Aşama | Durum | Detay |
|-------|-------|-------|
| Mahkeme (TASK modu) | ✅ APPROVED | %95 güven, browserless ile güvenli bulundu |
| smolagents CodeAgent | ✅ Başarılı | `web_fetch` → `web_extract_title` → "Example Domain" |
| Browserless:3001 | ✅ Bağlı | Headless Chrome üzerinden sayfa açıldı |
| Mem0 kaydı | ✅ | Başarılı görev hafızaya yazıldı |

### K2: Hata Enjeksiyonu ve Kurtarma ✅

**Test kümesi:** 6 test, 6 başarılı (%100)

| # | Test | Harness Stratejisi | Sonuç |
|---|------|-------------------|-------|
| 1 | ConnectionError | `_retry_with_backoff` (2s→4s→8s) | 3 deneme, kontrollü pes |
| 2 | Bozuk Araç (RuntimeError) | `_generic_retry` | CodeAgent iç hatayı yakaladı |
| 3 | Ulaşılamaz URL (DNS yok) | — | Anlamlı hata mesajı döndü |
| 4 | Orchestrator Hata Akışı | Mahkeme → REJECTED | Güvenlik filtresi çalıştı |
| 5 | TimeoutError | `_retry_with_backoff` | 3 deneme, kontrollü pes |
| 6 | ValueError | `_fix_value_error` | 3 deneme, kontrollü pes |

---

## Faz 2: Semantik Bellek (Mem0 Gerçek Entegrasyonu) ✅

### Yapılandırma

| Bileşen | Teknoloji | Detay |
|---------|-----------|-------|
| Bellek Motoru | **mem0ai v2.0.10** | Gerçek API, vektör tabanlı |
| LLM (fact extraction) | deepseek-v4-pro | LiteLLM proxy → `localhost:4000/v1` |
| Embedding | **FastEmbed** | Yerel, `BAAI/bge-small-en-v1.5` (384 boyut) |
| Vector Store | **Qdrant** | Gömülü mod, `altyapi/mem0_data/qdrant` |
| History DB | SQLite | `altyapi/mem0_data/mem0_history.db` |

### K3: 3 Görev + Semantik Hatırlama ✅

**Test:** Faz 2 kabul testi (`python orchestrator.py faz2-test`)

| Görev | İşlem | Sonuç | Bellek Durumu |
|-------|-------|-------|---------------|
| 1 | example.com başlık | ✅ `"Example Domain"` | Henüz anı yok (ilk görev) |
| 2 | httpbin.org/headers | ✅ 503 — kontrollü hata | Anı indeksleniyor... |
| 3 | example.com ekran görüntüsü | ✅ 19,343 bytes PNG | **1 anı bulundu** (httpbin) |
| 4 | **"Önceki görevleri hatırlıyor musun?"** | — | **2 anı bulundu!** |

**Bulunan anılar (4. adım):**
```
[1] (0.34) "User successfully captured a screenshot of https://example.com,
           resulting in a 19,343-byte image."
[2] (0.32) "User attempted to fetch JSON from https://httpbin.org/headers
           on July 1, 2026, but the server returned a 503 Service Unavailable."
```

### Yeni Yetenekler

- **`hatirla_ve_hatirlat()`** — Her görev öncesi otomatik semantik arama
- **`self.mem0.hatirla(query)`** — Vektör tabanlı anı araması
- **`self.mem0.kaydet(content)`** — LLM destekli olgu çıkarımı (fact extraction)
- **Mahkeme'ye geçmiş bağlam iletimi** — Benzer görevlerin sonuçları karar sürecine dahil edilir
- **CLI: `python orchestrator.py hatirla SORGU`** — Manuel anı araması
- **CLI: `python orchestrator.py faz2-test`** — Otomatik kabul testi

### Bilinen Sorunlar

- **9router modeli kapalı** — upstream bağlantı hatası, `deepseek-v4-pro` fallback olarak kullanılıyor
- **Mem0 extraction hatası** — `Error parsing extraction response: 'NoneType' object has no attribute 'strip'`. Bazı LLM yanıtları Mem0'ın beklediği JSON formatında değil. Anılar yine de kaydediliyor (raw text fallback).
- **spaCy NLP eksik** — `pip install mem0ai[nlp]` ile kurulursa daha iyi olgu çıkarımı yapılır
- **Qdrant kapanış uyarısı** — `sys.meta_path is None` harmless shutdown hatası

---

## Faz 3: browser-use Entegrasyonu ✅

### K4: browser-use Agent + Browserless CDP ✅

**Test:** `example.com aç, başlık döndür — aynı test, yeni araç`

| Aşama | Durum | Detay |
|-------|-------|-------|
| browser-use paketi | ✅ | v0.13.2, `browser-use-main` reposundan |
| CDP bağlantısı | ✅ | `ws://localhost:3001` (browserless) |
| Agent çalıştırma | ✅ | 2 adım, 3.1s, "Example Domain" |
| LLM entegrasyonu | ✅ | deepseek-v4-pro (LiteLLM proxy) |

### Değişen Dosyalar

| Dosya | Değişiklik | Açıklama |
|-------|-----------|----------|
| `mudahale/browser_use_bridge.py` | Güncellendi | `dont_force_structured_output=True` — Anthropic thinking mode + tool_choice çakışması çözüldü |
| `mudahale/web_tools.py` | Yeniden yazıldı | 4 araç: `web_fetch`, `web_extract_title`, `web_screenshot`, `web_navigate` — hepsi browser-use Agent kullanır |
| `orchestrator.py` | Güncellendi | `web_navigate` aracı eklendi, Mahkeme prompt'u güncellendi |

### browser-use Bridge Mimarisi

```
orchestrator.py
    │
    ├─ Web görevi → BrowserUseBridge.calistir(gorev)
    │   ├─ ChatOpenAI (deepseek-v4-pro @ LiteLLM :4000/v1)
    │   ├─ BrowserSession (cdp_url=ws://localhost:3001)
    │   └─ Agent.run_sync(max_steps=15)
    │
    └─ Kod görevi → smolagents CodeAgent + web_tools
        ├─ web_fetch(url)        → BrowserUseBridge.calistir(...)
        ├─ web_extract_title(url)→ BrowserUseBridge.calistir(...)
        ├─ web_screenshot(url)   → BrowserUseBridge.calistir(...)
        └─ web_navigate(url, act)→ BrowserUseBridge.calistir(...)
```

### Çözülen Sorunlar

- **Anthropic thinking mode + tool_choice:** `dont_force_structured_output=True` + `add_schema_to_system_prompt=True` ile şema tool_choice yerine system prompt'a kondu
- **frequency_penalty uyumsuzluğu:** `frequency_penalty=None` ile parametre gönderilmiyor
- **Windows/WSL Python:** Tüm testler WSL `.venv` içinde çalışıyor

---

## Mimari Durum (Faz 3 Sonu)

```
dijital-varlik/
├── orchestrator.py          ✅ dusun_ve_karar_ver() + browser-use + smolagents
├── karar/
│   ├── mahkeme_engine.py    ✅ claim/task modu, 4 rol
│   ├── harness.py           ✅ 6 hata stratejisi, exponential backoff
│   └── smolagents_bridge.py ✅ CodeAgent + LiteLLM proxy
├── mudahale/
│   ├── web_tools.py            ✅ 4 araç (browser-use Agent tabanlı)
│   └── browser_use_bridge.py   ✅ Browserless CDP + LiteLLM proxy
├── altyapi/
│   ├── mem0_bridge.py       ✅ Gerçek Mem0 (FastEmbed + Qdrant + LiteLLM)
│   ├── letta_bridge.py      ✅ Oturum yönetimi (dosya fallback)
│   └── litellm_bridge.py    ✅ LiteLLM proxy, fallback model
├── config/
│   ├── config.py            ✅ Merkezi konfigürasyon
│   └── .env                 ✅ API anahtarları
├── scripts/
│   ├── hata_enjeksiyon_testi.py  ✅ 6 testli hata test paketi
│   ├── mem0_smoke_test.py        ✅ Mem0 duman testi
│   └── test_models.py            ✅ Model durumu kontrolü
└── docs/
    └── hata_enjeksiyon_raporu.json  ✅ Makine-okunur test raporu
```

### Servis Durumu

| Servis | Adres | Durum |
|--------|-------|-------|
| LiteLLM Proxy | localhost:4000 | ✅ deepseek-v4-pro, deepseek-v4-flash |
| 9router (LiteLLM üzerinden) | localhost:4000 | ❌ Upstream bağlantı hatası |
| Browserless | localhost:3001 | ✅ Headless Chrome |
| Mem0 (Qdrant) | Yerel dosya | ✅ Gömülü mod, 384-d vektör |
| Mem0 (FastEmbed) | Yerel | ✅ BAAI/bge-small-en-v1.5 |
| Letta | localhost:8283 (EC2) | ⏳ Dosya fallback |

---

## Çekirdek Akış (Faz 2)

```
Kullanıcı Görevi
    │
    ▼
dusun_ve_karar_ver(gorev, context)
    │
    ├─ [0] 🧠 Bellek Taraması (YENİ)
    │   └─ Mem0.hatirla(gorev) → ilgili geçmiş anılar
    │
    ├─ [1/3] ⚖️  Mahkeme (TASK modu)
    │   ├─ Geçmiş anılar bağlam olarak eklenir
    │   ├─ Savcı → Savunma → Şüpheci → Hakim
    │   └─ APPROVED / REJECTED / NEEDS_MORE_EVIDENCE
    │
    ├─ [2/3] 🤖 APPROVED → smolagents CodeAgent
    │   ├─ web_fetch / web_extract_title / web_screenshot
    │   ├─ Browserless:3001
    │   └─ Harness: hata → strateji → retry (max 3)
    │
    └─ [3/3] 📤 Sonuç
        ├─ Mem0.add() → LLM olgu çıkarımı → Qdrant vektör indeksi
        ├─ Letta → oturum durumu
        └─ Kullanıcıya yanıt
```

---

## Sonraki Adımlar

- [x] **Faz 1-4:** Mahkeme, Mem0, Browser Use, BettaFish — tamam
- [x] **Faz 8: Agentik Dongu** — 11 bilesen tek dongude birlesik
- [x] **Agent S** — Windows masaustu koprusu (TCP :9999) canli
- [x] **Ses cikisi** — espeak fallback hazir
- [ ] **OpenClaw + Agent-Reach** — repolar klonlanacak
- [ ] **llama.cpp + LocalAI** — tamamen internetsiz calisma
- [ ] **GPU/NVIDIA surucusu** — Qwen3-VL, F5-TTS icin
- [ ] **Pipecat gercek ses akisi** — F5-TTS GPU'suz calisamaz

---

## Bilinen Sorunlar / Temizlik Gerekenler

**Son güncelleme:** 2026-07-04

### 1. Duplicate Ana Dosyalar
- **orchestrator.py (499 satır)** - Faz 3, DEPRECATED olarak işaretlendi
- **agentik_dongu.py (821 satır)** - Faz 8, gerçek ana dosya, 11+ bileşenli

**Durum:** orchestrator.py dosya başına "DEPRECATED" yorumu eklendi.

**Aksiyon:** agentik_dongu.py'yi resmi ana dosya olarak belgele, orchestrator.py'yi sil veya archive/ dizinine taşı.

### 2. Duplicate mahkeme_engine.py
- **karar/mahkeme_engine.py** - Canonical versiyon, config.config entegreli
- **mahkeme/mahkeme_engine.py** - Eski versiyon, KULLANILMIYOR olarak işaretlendi

**Durum:** mahkeme/mahkeme_engine.py dosya başına "KULLANILMIYOR" yorumu eklendi.

**Aksiyon:** mahkeme/ dizinini sil veya archive/ dizinine taşı.

### 3. Bridge Duplikasyonları

#### OpenClaw Bridge
- **mudahale/openclaw_bridge.py (60 satır)** - ✅ KAPSAMLI: subprocess, mesaj_gonder, durum
- **agentik_dongu.py içinde (satır 200-224)** - ❌ STUB: sadece temel methodlar

**Sonuç:** mudahale/openclaw_bridge.py KULLANILMALI, built-in sınıf silinmeli

#### AgentReach Bridge
- **mudahale/agentreach_bridge.py (48 satır)** - ✅ KAPSAMLI: kurulu_mu, timestamp, durum
- **agentik_dongu.py içinde (satır 230-249)** - ❌ STUB: basit kontroller

**Sonuç:** mudahale/agentreach_bridge.py KULLANILMALI, built-in sınıf silinmeli

#### Skyvern Bridge
- **mudahale/skyvern_bridge.py (82 satır)** - ✅ TAM ENTEGRASYON hazır
- **agentik_dongu.py** - ❌ HİÇ KULLANILMIYOR

**Sonuç:** agentik_dongu.py routing tablosuna EKLENMELİ (web görevleri için browser-use ile birlikte)

#### BettaFish Bridge
- **mudahale/bettafish_bridge.py** - ✅ İzole .venv_betta entegrasyonu
- **agentik_dongu.py satır 347** - ✅ ZATEN DOĞRU: conditional import kullanılıyor

**Sonuç:** Değişiklik gerekmiyor, doğru kullanılıyor.

### 4. İki Farklı Ses Mimarisi

#### Mimari A: ses_odasi.py
- FastAPI WebRTC sunucusu (port 8081)
- HTML tarayıcı arayüzlü
- Mikrofon → Whisper STT → LLM → espeak TTS
- **Standalone servis**

#### Mimari B: agentik_dongu.py
- Doğrudan algi_stt + algi_tts import
- WebRTC yok, tarayıcı arayüzü yok
- **Built-in entegrasyon**

**Durum:** İki yaklaşım **entegre değil**, paralel uygulamalar.

**Aksiyon:** Karar gerekli - ses_odasi.py'yi mi yoksa doğrudan entegrasyonu mu kullanmak istiyoruz? Ya birini sil, ya ikisini birleştir.

### 5. STATUS.md Yanıltıcı İfadeler

**Sorun:** "Tum zincir canli" ifadesi mevcut ama hiçbir servis çalışmıyor (ps aux kontrolü boş).

**Gerçek:** STATUS.md son test çalıştırmasını (2026-07-03 15:30) tarif ediyor, şuanki durumu değil.

**Aksiyon:** STATUS.md başlığını "Son Test Durumu" olarak değiştir, çalışan servis listesini ayrı bir bölüm yap.

### 6. EC2 Servisleri Doğrulanamıyor

**Sorun:** `ssh ubuntu@ip-172-31-28-59` hostname çözülemiyor (özel IP).

**Aksiyon:** SSH config veya VPN kurulumu gerekebilir. EC2 servislerinin durumu doğrulanmalı.

---

**Detaylı karşılaştırma:** BRIDGE_COMPARISON.md dosyasına bakın.
