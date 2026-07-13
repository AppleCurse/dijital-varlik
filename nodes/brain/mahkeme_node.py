"""
Brain: Mahkeme Node — 4 rollerli karar motoru.
Gorev onayi ve sonuc dogrulamasi yapar.
"""
from nodes import register

register("mahkeme", "brain", "nodes.brain.mahkeme_node",
         description="Hakikat Mahkemesi — 4 rol (Savci, Savunma, Supheci, Hakim)",
         deps=["karar.mahkeme_engine"])


class MahkemeNode:
    def __init__(self):
        self._ready = False
        self._mahkeme = None
        self._bootstrap()

    def _bootstrap(self):
        try:
            from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
            self._mahkeme = HakikatMahkemesi(llm=LLMClient())
            self._ready = True
        except Exception as e:
            print(f"[MahkemeNode] Bootstrap failed: {e}")

    def hazir_mi(self) -> bool:
        return self._ready

    def yargila(self, claim: str, context: str = "", mode: str = "task"):
        if not self._ready:
            return None
        return self._mahkeme.yargila(claim, context, mode)


_mahkeme_instance = None


def get_mahkeme_node():
    global _mahkeme_instance
    if _mahkeme_instance is None:
        _mahkeme_instance = MahkemeNode()
    return _mahkeme_instance
