"""
Arac Kayit Defteri (Tool Registry)
Tum bridge'leri tek bir yerden yonetir.
Auto-discovery ile yeni arac eklenince otomatik tanir.
"""
from typing import Dict, List, Callable, Optional
from pathlib import Path
import importlib

_tools: Dict[str, dict] = {}


def register(name: str, factory: Callable, category: str = "general", **meta):
    """Bir arac fabrikasini kaydet."""
    _tools[name] = {
        "name": name,
        "factory": factory,
        "category": category,
        "meta": meta,
    }


def get(name: str):
    """Isme gore arac getir (lazy init)."""
    t = _tools.get(name)
    if t:
        if "instance" not in t:
            t["instance"] = t["factory"]()
        return t["instance"]
    return None


def list_tools(category: str = None) -> List[dict]:
    if category:
        return [t for t in _tools.values() if t["category"] == category]
    return list(_tools.values())


# ================================================================
# Auto-register known bridges
# ================================================================

def _register_known():
    # smolagents
    try:
        from karar.smolagents_bridge import get_smol
        register("smolagents", lambda: get_smol(), "action",
                 description="Code Agent motoru")
    except Exception:
        pass

    # browser-use
    try:
        from mudahale.browser_use_bridge import get_browser_use
        register("browser-use", get_browser_use, "action",
                 description="Otonom tarayici kontrolu")
    except Exception:
        pass

    # Mem0
    try:
        from altyapi.mem0_bridge import get_mem0
        register("mem0", get_mem0, "memory",
                 description="Semantik bellek")
    except Exception:
        pass

    # Letta
    try:
        from altyapi.letta_bridge import get_letta
        register("letta", get_letta, "memory",
                 description="Kalici oturum bellegi")
    except Exception:
        pass

    # BettaFish
    try:
        from mudahale.bettafish_bridge import BettaFishBridge
        register("bettafish", lambda: BettaFishBridge(), "intelligence",
                 description="Sosyal medya istihbarati")
    except Exception:
        pass

    print(f"[tools] {len(_tools)} arac kaydedildi: {list(_tools.keys())}")


_register_known()
