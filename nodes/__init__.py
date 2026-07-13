"""
Dijital Varlik — Moduler Node Sistemi
Her node kendi kendini kesfeder ve kaydeder (auto-discovery).
"""
from pathlib import Path
from typing import Dict, List, Optional
import importlib
import sys

_registry: Dict[str, dict] = {}


def register(name: str, node_type: str, module_path: str, **meta):
    """Bir node'u global registry'ye kaydet."""
    _registry[name] = {
        "name": name,
        "type": node_type,
        "module": module_path,
        "meta": meta,
        "active": False,
    }


def discover():
    """Tum node alt paketlerini tara ve kaydet."""
    root = Path(__file__).parent
    for category in ["sensory", "brain", "action", "memory"]:
        cat_path = root / category
        if not cat_path.exists():
            continue
        for py_file in cat_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            mod_name = f"nodes.{category}.{py_file.stem}"
            try:
                importlib.import_module(mod_name)
            except Exception as e:
                print(f"[nodes] {mod_name} yuklenemedi: {e}")


def list_nodes(node_type: str = None) -> List[dict]:
    """Kayitli node'lari listele."""
    if node_type:
        return [n for n in _registry.values() if n["type"] == node_type]
    return list(_registry.values())


def get_node(name: str) -> Optional[dict]:
    return _registry.get(name)


# Otomatik kesif
discover()
