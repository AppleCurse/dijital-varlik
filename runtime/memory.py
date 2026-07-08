"""
UnifiedMemory — Tüm bellek sağlayıcılarını tek arayüzde birleştirir.

Mem0 (semantik) + Letta (oturum) + ChromaDB (doküman).

Kullanım:
    from runtime.memory import memory
    anilar = memory.search("merhaba", scope="hepsi")
    memory.store("yeni bilgi", scope="semantic")
"""
from typing import Any, Dict, List, Optional


class UnifiedMemory:
    """
    Tek bellek arayüzü. Alt sistemlerin detaylarını gizler.

    Scope seçenekleri:
    - "semantic" → Mem0
    - "session"  → Letta
    - "document" → ChromaDB (ATOM üzerinden)
    - "all"      → Hepsi
    """

    def __init__(self):
        self._mem0 = None
        self._letta = None
        self._chroma = None
        self._ready = False

    def wire(self, mem0=None, letta=None, chroma=None):
        """Bağımlılıkları bağla (RuntimeKernel tarafından çağrılır)."""
        self._mem0 = mem0
        self._letta = letta
        self._chroma = chroma
        self._ready = True

    @property
    def ready(self) -> bool:
        return self._ready

    # ── Arama ──

    def search(self, query: str, scope: str = "all", limit: int = 10) -> List[Dict]:
        """Tüm belleklerde semantik arama."""
        results = []
        if scope in ("all", "semantic") and self._mem0:
            try:
                results += self._mem0.hatirla(query, limit=limit) or []
            except Exception:
                pass
        if scope in ("all", "document") and self._chroma:
            try:
                results += self._chroma.ara(query, limit=limit) or []
            except Exception:
                pass
        return results[:limit]

    # ── Kaydetme ──

    def store(self, content: str, scope: str = "semantic", metadata: Dict = None) -> bool:
        """Belleğe kaydet."""
        ok = False
        if scope in ("all", "semantic") and self._mem0:
            try:
                self._mem0.kaydet(content, metadata)
                ok = True
            except Exception:
                pass
        return ok

    # ── Oturum ──

    def session_start(self, session_id: str, metadata: Dict = None) -> bool:
        if self._letta:
            try:
                self._letta.oturum_baslat(session_id, metadata)
                return True
            except Exception:
                pass
        return False

    def session_end(self, session_id: str) -> bool:
        if self._letta:
            try:
                self._letta.oturum_kapat(session_id)
                return True
            except Exception:
                pass
        return False

    def session_update(self, session_id: str, state: Dict) -> bool:
        if self._letta:
            try:
                self._letta.agent_durumu_kaydet(session_id, state)
                return True
            except Exception:
                pass
        return False

    # ── Olay ──

    def log_event(self, description: str, event_type: str = "info", level: str = "normal"):
        if self._mem0:
            try:
                self._mem0.olay_kaydet(description, event_type, level)
            except Exception:
                pass


# Global singleton
memory = UnifiedMemory()
