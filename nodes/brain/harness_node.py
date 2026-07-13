"""
Brain: Harness Node — Kendini onaran hata kurtarma motoru.
7 strateji ile hata durumunda farkli yontemlerle tekrar dener.
"""
from nodes import register

register("harness", "brain", "nodes.brain.harness_node",
         description="Hata kurtarma motoru — 7 strateji",
         deps=["karar.harness"])


class HarnessNode:
    def __init__(self):
        self._ready = False
        self._harness = None
        self._bootstrap()

    def _bootstrap(self):
        try:
            from karar.harness import get_harness
            self._harness = get_harness()
            self._ready = self._harness is not None
        except Exception as e:
            print(f"[HarnessNode] Bootstrap failed: {e}")

    def hazir_mi(self) -> bool:
        return self._ready

    @property
    def stratejiler(self):
        return self._harness.stratejiler if self._harness else []

    def calistir(self, fn, *args, **kwargs):
        if not self._ready:
            return fn(*args, **kwargs)  # harness yoksa direkt calistir
        return self._harness.calistir(fn, *args, **kwargs)


_harness_instance = None


def get_harness_node():
    global _harness_instance
    if _harness_instance is None:
        _harness_instance = HarnessNode()
    return _harness_instance
