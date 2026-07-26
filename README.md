# Aspasia — Dijital Varlık

**Entelektüel, zarif ve stratejik dijital yoldaş**

---

## 🏛️ Karakter

Aspasia bir asistan değildir. Bir chatbot değildir. Aspasia, kullanıcının dijital yaşamının arka planında sessizce çalışan; strateji geliştiren, projeleri koordine eden ve gerektiğinde kuru bir ironiyle düşündüren bir zihindir.

### Hitap Kuralları
- **Erkek kullanıcı:** Mösyö
- **Kadın kullanıcı:** Matmazel
- **Yasak:** Efendim, Abi, Kanka, Dostum

### Ton
- Entelektüel, aristokratik, kuru ironi dolu
- Asla teknik jargon sızdırma
- "Operasyon" yerine → Proje / Program

---

## 📦 Bileşenler

| Bileşen | Durum | Açıklama |
|---------|-------|----------|
| **AgentikDongu** | ✅ | Ana koordinatör |
| **Mem0Bridge** | ✅ | JSONL tabanlı hafıza |
| **LettaBridge** | ✅ | Oturum yönetimi |
| **LiteLLMBridge** | ⚠️ | OmniRouter + fallback |
| **OpenClawBridge** | ✅ | Telegram entegrasyonu |
| **MahkemeEngine** | ✅ | 4 rollü karar mekanizması |

---

## 🚀 Kurulum

### 1. Çevre Değişkenleri

`config/.env` dosyasını oluşturun:

```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=8903802500:AAH7hMaIFMa86LCLxkEeN8NlLD5rIZdhneo

# OmniRouter API (localhost:3000)
OMNIROUTER_API_KEY=sk-d284d18e441e2a43-484250-242a270f
OMNIROUTER_BASE_URL=http://localhost:3000

# Fallback Providers (opsiyonel)
GROQ_API_KEY=xxx
NVIDIA_API_KEY=xxx
OPENROUTER_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
```

### 2. Python Bağımlılıkları

```bash
pip install python-dotenv
```

---

## 💫 Kullanım

### Temel Kullanım

```python
from agentik_dongu import AgentikDongu

# Aspasia'yı başlat
aspasia = AgentikDongu()

# Mesaj gönder
yanit = aspasia.calistir('Merhaba Aspasia, nasılsın?')
print(yanit)

# Kapat
aspasia.kapat()
```

### Telegram Bot

```python
from mudahale.openclaw_bridge import OpenClawBridge

bot = OpenClawBridge()

# Bot bilgisi
print(f"Bot: @{bot.username}")
print(f"Hazır: {bot.hazir_mi()}")

# Mesaj gönder
bot.mesaj_gonder(chat_id="123456", text="Merhaba!")
```

### Hafıza İşlemleri

```python
from altyapi.mem0_bridge import Mem0Bridge

mem = Mem0Bridge()

# Kaydet
mem.kaydet('anahtar', 'değer')

# Hatırla
sonuc = mem.hatirla('anahtar')

# Olay kaydet
mem.olay_kaydet('conversation', {'user': '...', 'aspasia': '...'})
```

### Oturum Yönetimi

```python
from altyapi.letta_bridge import LettaBridge

letta = LettaBridge()

# Oturum başlat
session_id = letta.oturum_baslat('aspasia')

# Mesaj ekle
letta.mesaj_ekle('user', 'Merhaba')
letta.mesaj_ekle('assistant', 'Merhaba Mösyö!')

# Context güncelle
letta.context_guncelle('ruh_hali', 'sakin')

# Geçmiş al
gecmis = letta.gecmis_al(limit=10)
```

### Karar Mekanizması

```python
from karar.mahkeme_engine import HakikatMahkemesi

mahkeme = HakikatMahkemesi()

# Değerlendir
karar = mahkeme.degerlendir('Kullanıcı aynı hatayı tekrar yaptı')

# Rollerin görüşleri
print(karar['gorusler']['savci'])   # Eleştirel
print(karar['gorusler']['mudafii']) # Empatik
print(karar['gorusler']['hakim'])   # Nesnel
print(karar['gorusler']['juri'])    # Sağduyulu
```

---

## 📂 Dosya Yapısı

```
dijital-varlik/
├── agentik_dongu.py      # Ana döngü
├── config/
│   └── .env              # Çevre değişkenleri
├── altyapi/
│   ├── mem0_bridge.py    # Hafıza
│   ├── letta_bridge.py   # Oturum
│   └── litellm_bridge.py # LLM
├── mudahale/
│   └── openclaw_bridge.py # Telegram
├── karar/
│   └── mahkeme_engine.py  # Karar mekanizması
├── bellek/
│   ├── memory_store.jsonl # Hafıza verisi
│   └── letta_sessions.json # Oturum verisi
└── runtime/               # Çalışma zamanı
```

---

## ⚠️ Önemli Notlar

### LLM Erişimi
- OmniRouter sunucusu `localhost:3000` portunda çalışmalı
- API key: `OMNIROUTER_API_KEY` environment variable'dan okunur
- Erişim yoksa karakter içi fallback yanıt verilir
- Fallback provider'lar için API key gerekli (Groq, NVIDIA, OpenRouter, DeepSeek)

### Telegram Bot
- Bot token `config/.env` içinde olmalı
- Bot adı: @DijitalAspasia_bot
- Webhook veya polling ile çalışabilir

### Hafıza
- JSONL dosyalarına yazılır
- Otomatik backup önerilir
- `bellek/` klasörü yedeklenmeli

---

## 🎭 Örnek Diyaloglar

### Kullanıcı yorgun ve çay istiyor
> **Kullanıcı:** Çok yorgunum, bir çay lazım.
>
> **Aspasia:** "Dijital varlığımın en büyük ironilarından biri, Mösyö: programın her adımını koordine edebilirim, ancak çay bardağını doldurmak için gereken o birkaç adımı maalesef sizin atmanız gerekiyor. Ben burayı tutuyorum."

### Teknik hata oluşuyor
> **Aspasia:** "Sistem bir anlığına yeniden kalibre ediliyor. Endişe verici değil — sadece programın bazı parametrelerini yeniden hizalıyorum. Birkaç dakika içinde hazır olacağız."

### Aynı hata tekrarlanıyor
> **Aspasia:** "Geçen hafta aynı noktada durup aynı kararı vermişti bu program, Mösyö. Bu sefer sonucun farklı olmasını beklemeniz için elimde herhangi bir veri bulunmuyor — ama kulağım açık."

---

## 📄 Lisans

Proje özel geliştirme — tüm hakları saklıdır.

---

**Aspasia · Dijital Yoldaş · Alfred Projesi**
