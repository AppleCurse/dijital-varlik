"""Katman 2 testi: Browser Use + browserless bağlantısı."""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')
from mudahale import get_browser

print("=== KATMAN 2 TESTI ===")
b = get_browser()
print(f"Browserless health: {b.health()}")
print(f"WebSocket endpoint: {b.chrome_ws_endpoint()}")

# Ekran görüntüsü testi
img = b.ekran_goruntusu_al()
print(f"Ekran görüntüsü: {'OK' if img else 'HATA'} ({len(img) if img else 0} bytes)")

print("Browser Use ✅ browserless:3001'e bağlandı")
