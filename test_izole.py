#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Izole test: Her bileşeni ayrı ayrı test et, hangisinin takıldığını bul.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    print("[1] IMPORT TESTI")
    try:
        from mudahale.web_tools import web_fetch, web_extract_title, web_screenshot, web_navigate
        print("    web_tools: OK")
    except Exception as e:
        print(f"    web_tools: HATA - {e}")
        return False
    try:
        from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
        print("    mahkeme_engine: OK")
    except Exception as e:
        print(f"    mahkeme_engine: HATA - {e}")
    try:
        from karar.harness import get_harness
        print("    harness: OK")
    except Exception as e:
        print(f"    harness: HATA - {e}")
    try:
        from karar.smolagents_bridge import get_smol
        print("    smolagents_bridge: OK")
    except Exception as e:
        print(f"    smolagents_bridge: HATA - {e}")
    try:
        from mudahale.browser_use_bridge import get_browser_use
        print("    browser_use_bridge: OK")
    except Exception as e:
        print(f"    browser_use_bridge: HATA - {e}")
    return True

def test_litellm():
    print("\n[2] LITELLM HEALTH")
    try:
        from altyapi.litellm_bridge import litellm
        t0 = time.time()
        ok = litellm.health()
        print(f"    litellm.health(): {ok} ({time.time()-t0:.2f}s)")
        models = litellm.models()
        print(f"    litellm.models(): {models}")
        return ok
    except Exception as e:
        print(f"    LITELLM HATA: {e}")
        return False

def test_mem0():
    print("\n[3] MEM0")
    try:
        from altyapi.mem0_bridge import get_mem0
        t0 = time.time()
        m = get_mem0()
        print(f"    mem0 init: {time.time()-t0:.2f}s, hazir={m.hazir_mi}")
        return m.hazir_mi
    except Exception as e:
        print(f"    MEM0 HATA: {e}")
        return False

def test_letta():
    print("\n[4] LETTA")
    try:
        from altyapi.letta_bridge import get_letta
        t0 = time.time()
        l = get_letta()
        print(f"    letta init: {time.time()-t0:.2f}s")
        return True
    except Exception as e:
        print(f"    LETTA HATA: {e}")
        return False

def test_mahkeme():
    print("\n[5] MAHKEME")
    try:
        from config.config import config
        from karar.mahkeme_engine import LLMClient
        client = LLMClient(config.LITELLM_URL, config.LITELLM_KEY)
        print(f"    LLMClient created: OK")
        return True
    except Exception as e:
        print(f"    MAHKEME HATA: {e}")
        return False

def test_browser_use():
    print("\n[6] BROWSER-USE BRIDGE")
    try:
        from mudahale.browser_use_bridge import get_browser_use
        t0 = time.time()
        b = get_browser_use()
        print(f"    browser_use init: {time.time()-t0:.2f}s, hazir={b.hazir_mi()}")
        return b.hazir_mi()
    except Exception as e:
        print(f"    BROWSER-USE HATA: {e}")
        return False

def test_smol():
    print("\n[7] SMOLAGENTS")
    try:
        from mudahale.web_tools import web_fetch, web_extract_title, web_screenshot, web_navigate
        from karar.smolagents_bridge import get_smol
        t0 = time.time()
        tools = [web_fetch, web_extract_title, web_screenshot, web_navigate]
        s = get_smol(tools=tools)
        print(f"    smol init: {time.time()-t0:.2f}s, hazir={s.hazir_mi()}")
        return s.hazir_mi()
    except Exception as e:
        print(f"    SMOL HATA: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("IZOLE BILESEN TESTI")
    print("=" * 60)
    t_start = time.time()

    test_imports()
    test_litellm()
    test_mem0()
    test_letta()
    test_mahkeme()
    test_browser_use()
    test_smol()

    print(f"\nToplam sure: {time.time()-t_start:.2f}s")
