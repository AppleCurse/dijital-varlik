# dijital-varlik TAM DURUM RAPORU
> **Tarih:** 2026-07-25 | **İnceleyen:** Claude Code | **Dosyalar:** agentik_dongu.py, docker-compose.yml, config/.env, config.py, litellm_bridge.py, mahkeme_engine.py, smolagents_bridge.py

---

## 1. YÖNETİCİ ÖZETİ

**Proje:** Dijital Varlık — 4 katmanlı otonom AI ajan sistemi (Algı → Müdahale → Karar → Altyapı)
**Ana dosya:** `agentik_dongu.py` (939 satır, Faz 8)
**Kritik sorun:** LLM bağlantısı kopuk → zincirin %90'ı test edilemiyor
**Düzeltme süresi:** ~15 dakika (2 değişken güncellemesi)

---

## 2. MEVCUT DURUM — `.env` ANALİZİ

### 2.1 Şu anki aktif ayarlar (`config/.env`)

```bash
LITELLM_URL="https://openrouter.ai/api/v1"        # ← OpenRouter kullanılıyor!
LITELLM_KEY="sk-or-v1-5629765b5008851be11ad..."    # ← OpenRouter key
MAHKEME_MODEL=dijitalvarlik                         # ← OpenRouter'da özel model
FALLBACK_MODEL=mycombo                              # ← OpenRouter'da özel model
DEEPSEEK_API_KEY=***GİZLİ_API_ANAHTARI***  # ← BOŞTA! Kullanılmıyor!
```

**BULGU:** `.env` zaten 9router'dan uzaklaşıp OpenRouter'a geçmiş. Ama sorun şu: `dijitalvarlik` modeli OpenRouter'da tanımlı olmadığı için çağrılar başarısız oluyor. DeepSeek API key'i `.env`'de DURUYOR ama hiçbir kod onu kullanmıyor!

### 2.2 Claude Code'un kullandığı (ÇALIŞAN):
```
Base URL: https://api.deepseek.com/anthropic
Model:    deepseek-v4-pro
Auth:     ***GİZLİ_API_ANAHTARI***
```

### 2.3 config.py'deki fallback mantığı:
```python
# .env'de LITELLM_URL yoksa → WSL2 Windows host IP'sini bul → http://{IP}:20128/v1
_ROUTER_HOST = os.getenv("ROUTER_HOST", _windows_ip())
LITELLM_URL = os.getenv("LITELLM_URL", f"http://{_ROUTER_HOST}:20128/v1")
```

---

## 3. LLM BAĞLANTI MİMARİSİ — 3 AYRI YOL

Hepsi aynı config'ten besleniyor (`config.LITELLM_URL` + `config.LITELLM_KEY`):

```
config/.env
    │
    ├── LITELLM_URL  ─────────────────────────────────────┐
    ├── LITELLM_KEY  ───────────────────────────────────┐ │
    └── MAHKEME_MODEL ───────────────────────────────┐  │ │
                                                     │  │ │
    ┌────────────────────────────────────────────────┤  │ │
    │                                                │  │ │
    ▼                                                ▼  ▼ ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│ 1. LLMClient    │  │ 2. LiteLLMBridge │  │ 3. SmolAgentBridge  │
│ (mahkeme_engine)│  │ (litellm_bridge) │  │ (smolagents_bridge) │
│                 │  │                  │  │                     │
│ OpenAI format   │  │ OpenAI format    │  │ LiteLLMModel        │
│ POST /chat/     │  │ POST /chat/      │  │ (smolagents kütp.)  │
│ completions     │  │ completions      │  │ f"openai/{model}"   │
│                 │  │                  │  │                     │
│ Fallback:       │  │ Fallback:        │  │ Fallback: yok       │
│ Anthropic /msg  │  │ fallback_model   │  │                     │
└─────────────────┘  └──────────────────┘  └─────────────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
     Mahkeme             Dashboard              smolagents
     (4 rol)             health check           CodeAgent
```

**Kritik:** 3 yol da `config.LITELLM_URL`'e bakıyor. Tek bir `.env` değişikliği hepsini düzeltir.

---

## 4. agentik_dongu.py — ANA DÖNGÜ DETAYI

### 4.1 6 Fazlı Akış

```python
class AgentikDongu:
    def calistir(self, gorev: str) -> Dict:
        # FAZ 0: Bellek — Mem0 semantik arama
        anilar = self.faz_bellek(gorev)

        # FAZ 1: Mahkeme (TASK) — Görev güvenli mi?
        mahkeme = self.faz_mahkeme_gorev(gorev, anilar)
        if mahkeme["verdict"] == "REJECTED": return  # ← HEmen red

        # FAZ 2: Rota — Hangi araç?
        rota = self.faz_rota(gorev)

        # FAZ 3: İcra — Harness korumalı çalıştır
        icra = self.faz_icra(gorev, rota)

        # FAZ 4: Mahkeme (CLAIM) — Sonuç doğru mu?
        mahkeme_claim = self.faz_mahkeme_claim(gorev, icra)

        # FAZ 5: Kayıt — Mem0 + Letta
        self.faz_kayit(gorev, sonuc, tum_fazlar)
```

### 4.2 Bağlantı kurma (`_baglan()`) sırası:
```python
# Satır 323: LLMClient oluştur (config.LITELLM_URL → OpenRouter)
self.llm = LLMClient(config.LITELLM_URL, config.LITELLM_KEY)

# Satır 324: LiteLLMBridge (aynı config)
self.litellm = litellm  # global instance

# Satır 327: Mahkeme (LLMClient enjekte edilir)
self.mahkeme = HakikatMahkemesi(llm=self.llm)

# Satır 349: smolagents (aynı config)
self.smol = get_smol(tools=self.web_tools)
```

### 4.3 İçerideki sorunlar:
- **Satır 351, 358-359:** Boş `pass` ifadeleri — yarım kalmış kod
- **Satır 198-246:** OpenClawBridge ve AgentReachBridge STUB olarak agentik_dongu.py İÇİNDE tanımlanmış. Ama `mudahale/openclaw_bridge.py` dosyası daha kapsamlı. **Duplikasyon.**
- **Satır 64-179:** AgentSBridge yine içeride — `mudahale/agent_s_server.ps1` var ama ayrı bridge dosyası yok.
- **Satır 796-823:** `toplu_test()` var ama test dosyaları kök dizinde dağınık.
- **Satır 829:** `durum()` metodu var, ama `hebo: False`, `airi: False`, `openhands: False` hep hardcoded.

### 4.4 Çalışan kısımlar (LLM'den bağımsız):
- `gorev_tipini_belirle()` — anahtar kelime tabanlı, LLM kullanmaz ✅
- `AgentSBridge` — TCP socket, LLM kullanmaz ✅
- `faz_kayit()` — Mem0 dosya fallback, LLM kullanmaz ✅
- `_get_tts()` — espeak-ng, LLM kullanmaz ✅
- `_fast_path_check()` — Mahkeme'de hızlı yol, LLM kullanmaz ✅

---

## 5. docker-compose.yml — SERVİS DURUMU

```yaml
services:
  9router:       # :20128 — LLM yönlendirici
    image: decolua/9router
    depends: yok
    healthcheck: curl /api/health

  litellm:       # :4000 — LLM proxy
    image: ghcr.io/berriai/litellm
    depends_on: 9router (service_healthy)  # ← 9router ÇALIŞMADAN LiteLLM başlamaz!
    config: ./litellm-config.yaml

  browserless:   # :3004 → container :3000
    image: browserless/chrome

  db:            # :5432 — PostgreSQL (BettaFish için)
    image: postgres:15-alpine
```

| Servis | Port | Docker İmaj | Durum |
|--------|------|-------------|-------|
| 9router | 20128 | decolua/9router | ❌ Docker çalışmıyor |
| LiteLLM | 4000 | ghcr.io/berriai/litellm | ❌ 9router'sız başlamaz |
| Browserless | 3004 | browserless/chrome | ❌ Docker çalışmıyor |
| PostgreSQL | 5432 | postgres:15-alpine | ❌ Docker çalışmıyor |

**Sorun:** `sudo service docker start` yapılmadığı için hiçbir container çalışmıyor. Ayrıca `litellm` container'ı `depends_on: 9router (service_healthy)` ile bağlı — 9router sağlıklı olmadan başlamaz.

---

## 6. KOPUK PARÇALAR — TAM LİSTE

### 🔴 Çalışmayı engelleyen (3 adet)

| # | Parça | Nedeni | Dosya/Satır |
|---|-------|--------|-------------|
| 1 | **LLM bağlantısı** | OpenRouter'da `dijitalvarlik` modeli yok → 401/auth hatası | `.env` L1-4 |
| 2 | **Docker** | `docker ps` başarısız, servisler kapalı | sistem |
| 3 | **Python .venv** | Bozuk symlink, `pip install` çalışmaz | `.venv/bin/python3` |

### 🟡 Yapısal sorunlar (7 adet)

| # | Parça | Detay |
|---|-------|-------|
| 4 | **Çift ana dosya** | `agentik_dongu.py` (939 satır, aktif) vs `orchestrator.py` (499, deprecated) |
| 5 | **Çift mahkeme** | `karar/mahkeme_engine.py` (canonical) vs `mahkeme/mahkeme_engine.py` (eski) |
| 6 | **Bridge duplikasyonu** | OpenClawBridge: `agentik_dongu.py:198` (stub) + `mudahale/openclaw_bridge.py` (kapsamlı) |
| 7 | **Bridge duplikasyonu** | AgentReachBridge: `agentik_dongu.py:228` (stub) + `mudahale/agentreach_bridge.py` yok |
| 8 | **Çift ses mimarisi** | `algi/ses_odasi.py` (WebRTC standalone) vs `algi/algi_stt.py + algi/algi_tts.py` |
| 9 | **Dağınık testler** | 11 test dosyası kök dizinde |
| 10 | **Boş pass'ler** | `agentik_dongu.py:351,358-359` — yarım kalmış kod blokları |

### 🟢 Sağlam parçalar (8 adet)

| # | Parça | Durum |
|---|-------|-------|
| 1 | Claude Code (DeepSeek proxy) | ✅ Çalışıyor |
| 2 | Tailscale + Funnel | ✅ `trrdg2.taile8a0f0.ts.net` |
| 3 | agentik_dongu.py (kod) | ✅ 939 satır, 6 fazlı döngü |
| 4 | mahkeme_engine.py (kod) | ✅ 560 satır, 4 rol, fast-path |
| 5 | harness.py (kod) | ✅ 6+ hata stratejisi |
| 6 | smolagents_bridge.py (kod) | ✅ CodeAgent hazır |
| 7 | browser_use_bridge.py (kod) | ✅ CDP bağlantısı hazır |
| 8 | TTS (espeak-ng) | ✅ Çalışıyor |

---

## 7. ÇÖZÜM — TAM İŞLEM PLANI

### ADIM 1: `.env` güncelle (5 dakika)

```diff
# config/.env
- LITELLM_URL="https://openrouter.ai/api/v1"
+ LITELLM_URL="https://api.deepseek.com/v1"

- LITELLM_KEY="sk-or-v1-5629765b5008851be11ad..."
+ LITELLM_KEY="***GİZLİ_API_ANAHTARI***"  # DEEPSEEK_API_KEY (zaten .env'de var!)

- MAHKEME_MODEL=dijitalvarlik
+ MAHKEME_MODEL=deepseek-chat

- FALLBACK_MODEL=mycombo
+ FALLBACK_MODEL=deepseek-chat
```

**Neden çalışır:** DeepSeek API OpenAI formatını destekler. LLMClient, LiteLLMBridge, SmolAgentBridge üçü de OpenAI `/chat/completions` endpoint'ine POST atar. DeepSeek API bu formatı native destekler. API key zaten `.env`'de mevcut. Claude Code'un kullandığı aynı servis (zaten çalıştığı kanıtlanmış).

### ADIM 2: Python ortamını düzelt (5 dakika)

```bash
cd ~/dijital-varlik
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install python-dotenv requests smolagents litellm
```

### ADIM 3: Bağlantıyı test et (2 dakika)

```bash
source .venv/bin/activate

# Test 1: Config doğru mu?
python3 -c "
from config.config import config
print('URL:', config.LITELLM_URL)
print('KEY:', config.LITELLM_KEY[:20] + '...')
print('MODEL:', config.MAHKEME_MODEL)
"

# Test 2: LLMClient direkt çağrı
python3 -c "
from karar.mahkeme_engine import LLMClient
llm = LLMClient()
r = llm.call('1+1 kac?', '1+1 kac?', max_tokens=50)
print('LLMClient:', r.get('content', r)[:100])
"

# Test 3: LiteLLMBridge health
python3 -c "
from altyapi.litellm_bridge import litellm
print('Health:', litellm.health())
print('Models:', len(litellm.models()))
"
```

### ADIM 4: Docker ve Browserless (3 dakika)

```bash
sudo service docker start
cd ~/dijital-varlik
docker compose up -d browserless  # sadece browserless, 9router/litellm'e gerek yok
curl http://localhost:3004/json/version
```

### ADIM 5: Tam zincir testi (5 dakika)

```bash
source .venv/bin/activate
python3 -c "
from agentik_dongu import AgentikDongu
dongu = AgentikDongu()
sonuc = dongu.calistir('https://example.com sitesinin basligini getir')
print('SONUC:', sonuc.get('status'), '-', sonuc.get('message', '')[:200])
dongu.kapat()
"
```

---

## 8. TEK ADIMDA DÜZELTME (KOPYALA-YAPIŞTIR)

```bash
# === TEK SEFERDE TÜM DÜZELTMELER ===

# 1. .env güncelle
cd ~/dijital-varlik
cp config/.env config/.env.yedek
sed -i 's|LITELLM_URL="https://openrouter.ai/api/v1"|LITELLM_URL="https://api.deepseek.com/v1"|' config/.env
sed -i 's|LITELLM_KEY="sk-or-v1.*"|LITELLM_KEY="***GİZLİ_API_ANAHTARI***"|' config/.env
sed -i 's|MAHKEME_MODEL=dijitalvarlik|MAHKEME_MODEL=deepseek-chat|' config/.env
sed -i 's|FALLBACK_MODEL=mycombo|FALLBACK_MODEL=deepseek-chat|' config/.env

# 2. Python venv
rm -rf .venv && python3 -m venv .venv
source .venv/bin/activate
pip install -q python-dotenv requests smolagents litellm

# 3. Test
python3 -c "
from karar.mahkeme_engine import LLMClient
r = LLMClient().call('1+1=?', '1+1=?', max_tokens=30)
print('LLM TEST:', 'OK' if r and 'error' not in r else 'FAIL')
"
```

---

## 9. SONRASI — TEMİZLİK PLANI

LLM zinciri çalıştıktan sonra yapılacaklar:

```bash
# Arşiv
mkdir -p archive
mv orchestrator.py archive/            # deprecated
mv mahkeme/ archive/                  # eski mahkeme dizini
mv *.bak archive/                     # yedekler
mv *.bozuk archive/                   # bozuklar
mv docker-compose.yml.bak archive/
mv litellm-config.yaml.bak archive/

# Testleri topla
mv test_*.py tests/
mv final_test.py tests/
mv check_models.py tests/
mv *_buton.py tests/

# __pycache__ temizle
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

---

## 10. ÖZET TABLO

| Metrik | Değer |
|--------|-------|
| Proje büyüklüğü | ~dijital-varlik/ dizini |
| Ana dosya | agentik_dongu.py (939 satır) |
| Python dosyası | 50+ (testler hariç) |
| Katman | 4 (Algı, Müdahale, Karar, Altyapı) |
| LLM bağlantı yolu | 3 (LLMClient, LiteLLMBridge, SmolAgentBridge) |
| API key | 14 adet .env'de, 12 farklı config'de |
| Docker servisi | 4 (9router, LiteLLM, Browserless, PostgreSQL) |
| Klon repo | 17 (7'si GPU bekliyor) |
| Ajan konfigürasyonu | 13 farklı dizinde |
| Çalışan tek şey | Claude Code (DeepSeek proxy) |
| Düzeltme için değişecek | .env'de 4 satır |
| Tahmini düzelme süresi | 15 dakika |
