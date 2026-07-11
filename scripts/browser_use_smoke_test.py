"""Quick smoke test for browser-use bridge."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from mudahale.browser_use_bridge import BrowserUseBridge

print("BrowserUseBridge baslatiliyor...")
b = BrowserUseBridge()
print(f"Hazir: {b.hazir_mi()}")

if b.hazir_mi():
    print("\nTest gorevi calistiriliyor: example.com basligi...")
    result = b.calistir("Go to https://example.com and tell me the page title. Return just the title text.")
    print(f"\nSonuc: {result}")
    if result and "Example" in str(result):
        print("\n✅ Browser-use bridge smoke test basarili!")
    else:
        print("\n⚠️ Sonuc alindi ama Example Domain icermiyor.")
else:
    print("❌ BrowserUseBridge baslatilamadi")
