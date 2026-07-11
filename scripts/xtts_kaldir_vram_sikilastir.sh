#!/bin/bash
# XTTS'i kaldır — sürekli bakım yükü, F5-TTS zaten daha iyi ve hazır.
# ============================================================

echo "=== XTTS kaldırılıyor (1.35GB disk kazancı) ==="
pip uninstall -y coqui-tts TTS 2>/dev/null
# Model dosyalarını da temizle (genelde ~/.local/share/tts veya ~/.cache/tts altında)
find ~ -iname "*xtts*" -type d 2>/dev/null | head -20
echo "Yukarıdaki klasörleri manuel kontrol edip rm -rf ile sil (otomatik silmiyorum, emin ol)"

echo ""
echo "=== ses.py / tts bridge'inde XTTS referanslarını F5-TTS'e yönlendir ==="
grep -rl "xtts\|coqui" --include="*.py" . 2>/dev/null
echo "Yukarıdaki dosyalarda xtts_bridge çağrılarını f5tts_bridge ile değiştir"

# ============================================================
# VRAM/RAM headroom sıkılaştırma
# ============================================================
# Mevcut durum: VRAM 3108MB/4096MB boş, RAM 3.8GB/7.7GB boş.
# Bu headroom yeni bir zincir (SadTalker/LivePortrait gibi) eklendiğinde
# GPU çakışmasına (senin daha önce belgelediğin sorun) geri döner.

echo ""
echo "=== gpu.py'de sıkı kilitleme öner ==="
cat <<'EOF'
# runtime/gpu.py içindeki GPU lock mantığına ekle:
# - Aynı anda yalnızca 1 model VRAM'de aktif olsun (mevcut zaten "locked" flag var)
# - Model boşta kaldığında (örn. 60sn kullanılmadıysa) otomatik VRAM'den boşalt (unload)
# - Yeni model her istendiğinde önce mevcut kilitli modeli unload et, sonra yükle
#
# Bu "sıralı model değişimi" (model swap) 4GB'lık kart için zorunlu —
# GTX 1650 asla 2 büyük modeli aynı anda tutamaz.
EOF

echo ""
echo "=== RAM için swap kontrolü ==="
free -h
echo "Eğer swap yoksa veya küçükse (WSL2 varsayılanı genelde düşük), .wslconfig'e ekle:"
cat <<'EOF'
[wsl2]
memory=6GB
swap=8GB
EOF
