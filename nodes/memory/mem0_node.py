"""
Memory: Mem0 Node — Semantik bellek (vektor tabanli).
Gecmis gorevleri hatirlar, benzer baglamlari bulur.
"""
from nodes import register

register("mem0", "memory", "nodes.memory.mem0_node",
         description="Semantik bellek (Mem0 — vektor tabanli)",
         deps=["altyapi.mem0_bridge"])


class Mem0Node:
    def __init__(self):
        self._ready = False
        self._mem0 = None
        self._bootstrap()

    def _bootstrap(self):
        try:
            from altyapi.mem0_bridge import get_mem0
            self._mem0 = get_mem0()
            self._ready = self._mem0.hazir_mi() if hasattr(self._mem0, 'hazir_mi') else True
        except Exception as e:
            print(f"[Mem0Node] Bootstrap failed: {e}")

    def hazir_mi(self) -> bool:
        return self._ready

    def hatirla(self, query: str, limit: int = 5):
        if not self._ready:
            return []
        return self._mem0.hatirla(query, limit) or []

    def kaydet(self, content: str, metadata: dict = None):
        if not self._ready:
            return False
        return self._mem0.kaydet(content, metadata)


_mem0_instance = None


def get_mem0_node():
    global _mem0_instance
    if _mem0_instance is None:
        _mem0_instance = Mem0Node()
    return _mem0_instance
