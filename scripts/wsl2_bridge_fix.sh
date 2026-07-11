# WSL2 Docker → Windows Host (9Router) Bridge Kopukluğu — Kalıcı Çözüm
#
# SORUN: Docker bridge (172.17.0.1) Windows host'taki 9Router'a (port 20128) ulaşamıyor.
# Şu anki "çözüm" (Python'un LiteLLM'i bypass edip 9Router'a direkt bağlanması) bir
# ÇÖZÜM DEĞİL, bir İDARE — LiteLLM proxy katmanının tüm faydalarını (rate limit,
# fallback, semantic cache, logging) kaybediyorsun.
#
# GERÇEK ÇÖZÜM: WSL2 "mirrored" networking modu (Windows 11 22H2+ gerekli).
# Mirrored modda WSL2, Windows'la AYNI ağ arayüzünü paylaşır — localhost her iki
# yönde de çalışır, bridge/NAT problemi tamamen ortadan kalkar.

# ============================================================
# ADIM 1 — Windows tarafında %UserProfile%\.wslconfig dosyasını oluştur/düzenle
# (PowerShell'de: notepad $env:UserProfile\.wslconfig)
# ============================================================

cat <<'EOF'
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
firewall=true

[experimental]
hostAddressLoopback=true
EOF

# ============================================================
# ADIM 2 — WSL2'yi tamamen kapat ve yeniden başlat (Windows PowerShell'de)
# ============================================================
# wsl --shutdown
# (birkaç saniye bekle, sonra WSL2'yi tekrar aç)

# ============================================================
# ADIM 3 — Doğrulama (WSL2 içinde)
# ============================================================
# Mirrored modda artık localhost:20128 doğrudan Windows'taki 9Router'a ulaşmalı:
echo "9Router testi:"
curl -s --max-time 3 http://localhost:20128/health || echo "HALA ULAŞMIYOR — Windows Defender Firewall'da 20128 portu için inbound kural gerekebilir"

echo ""
echo "LiteLLM Docker'ın 9Router'a ulaşımı testi:"
docker exec dijital-varlik_litellm_1 curl -s --max-time 3 http://localhost:20128/health || echo "Docker konteyner içinden hala ulaşmıyor — konteyner network_mode:host ile yeniden başlatılmalı"

# ============================================================
# ADIM 4 — Eğer hâlâ ulaşmıyorsa (bazı Windows sürümlerinde mirrored mode
# konteyner içinden localhost'u farklı yorumlayabilir): docker-compose'da
# network_mode: "host" ekle (LiteLLM servisi için)
# ============================================================
cat <<'EOF'
# docker-compose.yml içinde litellm servisine ekle:
services:
  litellm:
    network_mode: "host"   # bridge yerine host ağını kullan
    # ports: bloğunu host mode'da kaldırman gerekir (zaten host'un portlarını kullanır)
EOF
