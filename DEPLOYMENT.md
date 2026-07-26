# Aspasia - Deployment Rehberi

## ✅ Sistem Durumu (Güncel)

| Bileşen | Durum | Not |
|---------|-------|-----|
| AgentikDongu | ✅ Hazır | Ana koordinatör çalışıyor |
| Mem0Bridge | ✅ Hazır | JSONL hafıza aktif |
| LettaBridge | ✅ Hazır | Oturum yönetimi aktif |
| LiteLLMBridge | ⚠️ Beklemede | OmniRouter sunucusu gerekli |
| OpenClawBridge | ✅ Hazır | Telegram token set |
| MahkemeEngine | ✅ Hazır | 4 rol aktif |

## 📦 API Anahtarları (config/.env)

```bash
TELEGRAM_BOT_TOKEN=8903802500:AAH7hMaIFMa86LCLxkEeN8NlLD5rIZdhneo
OMNIROUTER_API_KEY=sk-d284d18e441e2a43-484250-242a270f
OMNIROUTER_BASE_URL=http://localhost:3000
```

## 🔧 Gerekli Adımlar

### 1. OmniRouter Sunucusunu Başlat

**Windows tarafında:**
- 9Router/OmniRouter uygulamasını aç
- Port 3000'de çalıştığından emin ol
- API key: `sk-d284d18e441e2a43-484250-242a270f`

**Doğrulama:**
```bash
curl http://localhost:3000/api/providers \
  -H "Authorization: Bearer sk-d284d18e441e2a43-484250-242a270f"
```

### 2. Fallback Provider'ları Ekle (Opsiyonel)

`.env` dosyasına ekle:
```bash
GROQ_API_KEY=gsk_xxx
NVIDIA_API_KEY=nvapi-xxx
OPENROUTER_API_KEY=sk-or-v1-xxx
DEEPSEEK_API_KEY=sk-xxx
```

### 3. Test Et

```bash
cd /workspace/dijital-varlik
source .venv/bin/activate

python3 -c "
from agentik_dongu import AgentikDongu
d = AgentikDongu()
print(d.calistir('Merhaba'))
d.kapat()
"
```

## 📂 GitHub'a Push

```bash
cd /workspace/dijital-varlik

# Remote ekle (kendi repo URL'nizi kullanın)
git remote add origin https://github.com/KULLANICI_ADI/dijital-varlik.git

# Push et
git push -u origin main
```

## 🎯 Kullanım

### Python
```python
from agentik_dongu import AgentikDongu
aspasia = AgentikDongu()
yanit = aspasia.calistir('Merhaba Aspasia!')
print(yanit)
aspasia.kapat()
```

### Telegram Bot
- Bot: @DijitalAspasia_bot
- Token: config/.env içinde
- Webhook veya polling ile çalışır

## 📊 Entegrasyon Oranı: %90

- ✅ 5/6 bileşen tam çalışır
- ⚠️ 1/6 bileşen sunucu bekliyor (LiteLLM)
- ❌ Voicebox, AlphaAvatar opsiyonel (gerekirse eklenebilir)
