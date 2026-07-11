"""Browserless bağlantı testi."""
import sys
sys.path.insert(0, '/home/administrator/dijital-varlik')
from mudahale.browser_bridge import get_browser

browser = get_browser()
print(f"Browserless URL : {browser.browserless_url}")
print(f"Health         : {'OK' if browser.health() else 'FAIL'}")
print(f"CDP Endpoint   : {browser.chrome_ws_endpoint()}")

# Screenshot test
import base64
img = browser.ekran_goruntusu_al()
print(f"Screenshot     : {'OK (' + str(len(img)) + ' bytes)' if img else 'FAIL'}")
if img:
    # Save to file for verification
    with open('/home/administrator/dijital-varlik/scripts/test_screenshot.png', 'wb') as f:
        f.write(img)
    print("Saved to scripts/test_screenshot.png")
