#!/usr/bin/env python3
"""
Test script: web_navigate import ve orchestrator.py durum kontrolü
"""
import sys
from pathlib import Path

print("=" * 60)
print("TEST 1: mudahale.web_tools import")
print("=" * 60)

try:
    from mudahale.web_tools import web_fetch, web_extract_title, web_screenshot, web_navigate
    print("✅ web_fetch:", web_fetch.name)
    print("✅ web_extract_title:", web_extract_title.name)
    print("✅ web_screenshot:", web_screenshot.name)
    print("✅ web_navigate:", web_navigate.name)
    print("\n✅ TÜM ARAÇLAR İMPORT EDİLDİ")
except ImportError as e:
    print(f"❌ IMPORT HATASI: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 2: orchestrator.py import")
print("=" * 60)

try:
    from orchestrator import DijitalVarlik
    print("✅ DijitalVarlik sınıfı import edildi")
except Exception as e:
    print(f"❌ ORCHESTRATOR IMPORT HATASI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST 3: DijitalVarlik başlatma (hızlı)")
print("=" * 60)

try:
    varlik = DijitalVarlik()
    print("\n✅ DijitalVarlik başarıyla başlatıldı")
    print(f"   Session ID: {varlik.session_id}")
    print(f"   Mahkeme: {'✅' if varlik.mahkeme else '❌'}")
    print(f"   smolagents: {'✅' if varlik.smol.hazir_mi() else '❌'}")
    print(f"   browser-use: {'✅' if varlik.browser_use.hazir_mi() else '❌'}")
    print(f"   Web araç sayısı: {len(varlik.web_tools)}")

    varlik.kapat()
except Exception as e:
    print(f"❌ DİJİTALVARLIK BAŞLATMA HATASI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TÜM TESTLER BAŞARILI")
print("=" * 60)
