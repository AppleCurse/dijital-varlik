# dijital-varlik — Mutlak Siber Organizma

Kendi kendine kod yazan, hatalarından ders alıp kendini onaran, fiziksel bilgisayara hükmeden,
dış dünyayı izleyen ve kararlarını "Hakikat Mahkemesi" mekanizmasıyla filtreleyen sıfır halüsinasyonlu
siber organizma projesi.

## Mimari (4 Katman)

### Katman 1: Algı (Bedensel Varlık — Görme, Duyma)
| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Arayüz/Beden | A.T.O.M / IRIS-AI / AIRI | Modüler yerel asistan işletim sistemi, WebGPU 3D avatar |
| Görme | Qwen2.5-VL | Kameradan ekranı/görüntüyü okuyup mantık yürütür |
| Ses (TTS) | F5-TTS, Qwen3-TTS | Ses klonlama (3sn), saf C motoru yedek |
| Ses (Gerçek Zamanlı) | Pipecat | Düşük gecikmeli gerçek zamanlı ses hattı |

### Katman 2: Fiziksel Müdahale (Fare, Klavye, Web)
| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Yerel Cihaz Kontrolü | Agent S / Open Interpreter | Fare ve klavyeyi doğrudan manipüle eder |
| Tarayıcı/Otonom Web | Browser Use / Skyvern | Otonom headless tarayıcı |
| Sosyal İstihbarat | BettaFish (MindSpider) / Agent-Reach | TikTok, Weibo, Reddit derin sosyal analiz |

### Katman 3: Karar Merkezi (Beyin)
| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Kod Yazan Otonomi | smolagents (Code-Agents) | Araç kullanmak için anında Python kodu yazıp çalıştırır |
| Kendini Onaran Döngü | Harness SDK / agentware | Hatayı algıla → strateji değiştir → kodu onarıp tekrar dene |
| Hakikat Mahkemesi | Minimal Viable Debate | Savcı, Savunma, Şüpheci, Hakim — %100 onaysız veri çıkışı yok |

### Katman 4: Ağ Geçidi ve Hafıza (Altyapı)
| Bileşen | Teknoloji | Rol |
|---------|-----------|-----|
| Router | Hebo Gateway / OmniRoute | Özelleştirilebilir routing/auth, ücretsiz token havuzu |
| Hafıza | Mem0 (bilgi grafiği) / Letta (kalıcı bellek) / Ontheia (yedek, pgvector) | Üçlü bellek katmanı |
| Kokpit | Open WebUI / Odysseus | Yerel, telemetrisiz yönetim paneli |

## Altyapı

- **Yerel PC (Windows 10):** Algı katmanı çalışır — A.T.O.M/Odysseus, Qwen2.5-VL, Pipecat, F5-TTS
- **EC2 Sunucusu:** `ubuntu@ip-172-31-28-59` — Ağır iş yükleri

### EC2'de Çalışan Servisler
| Port | Servis |
|------|--------|
| 22 | SSH |
| 3000 | Open WebUI |
| 3001 | Browserless |
| 8080 | Node |
| 9001 | Python3 |
| 20128, 20131 | 9Router (LLM yönlendirme) |
| 20241 | Cloudflared (webui.esnafalarm.com.tr) |
| 26945 | Node |

- **cidt-v2:** Bellek-ontoloji motoru
- **Kapalı:** Ollama (binary ve klasör yok)

## Çalışma Akışı (Aşama 2)

```
Algı (Yerel) → Aktarım (Hebo + OmniRoute → EC2) → Otonom Kodlama (smolagents)
→ Doğrulama (Mahkeme) → Aksiyon (Browser Use / Agent S) → Hafıza & Yanıt (Mem0 + Letta + AIRI + F5-TTS)
```

## Geliştirme Kuralları

1. **Her yeni özellik önce Hakikat Mahkemesi mantığıyla değerlendirilir:**
   - Savcı: "Bu özellik neden eklenmeli?"
   - Savunma: "Bu özellik neden riskli?"
   - Şüpheci: "Hangi kanıtlar eksik?"
   - Hakim: Nihai karar
2. **EC2'ya deploy etmeden önce yerelde test et.** smolagents kod üretimi her zaman sandbox'ta dener.
3. **Tüm kararlar Mem0 bilgi grafına yazılır.** Letta oturumlar arası kalıcılığı sağlar.
4. **Bağlantı bilgileri asla commit etme.** `.env` dosyasındadır, `.gitignore`'dadır.
5. **Dil:** Kod ve yorumlar İngilizce, dokümantasyon ve commit mesajları Türkçe.

## Dizin Yapısı (Hedef)

```
~/dijital-varlik/
├── algi/           # Katman 1 — Görme, ses, avatar
├── mudahale/       # Katman 2 — Agent S, Browser Use, BettaFish
├── karar/          # Katman 3 — smolagents, Harness, Mahkeme
├── altyapi/        # Katman 4 — Gateway, hafıza, kokpit
├── config/         # .env, ayar dosyaları
├── scripts/        # Kurulum ve deploy scriptleri
└── docs/           # Mimari kararlar, ADR'ler
```

## Sık Kullanılan Komutlar

```bash
# EC2'ya bağlan
ssh ubuntu@ip-172-31-28-59

# Open WebUI (EC2 üzerinde)
curl http://localhost:3000

# Browserless (EC2 üzerinde)
curl http://localhost:3001

# EC2 servis durumu
ssh ubuntu@ip-172-31-28-59 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```
