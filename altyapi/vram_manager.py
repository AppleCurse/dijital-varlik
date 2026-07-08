"""
VRAM Manager — Agresif GPU Bellek Yönetimi.

GTX 1650 (4.3 GB) için optimize. Modeller aynı anda GPU'da kalamaz.
Her model yüklemede öncekini boşaltır, torch.cuda.empty_cache() çakar.

Kullanım:
    from altyapi.vram_manager import vram

    # Modeli yükle (önceki varsa otomatik boşaltılır)
    model = vram.load("qwen", lambda: AutoModel.from_pretrained(...))

    # İşin bitince isteğe bağlı boşalt
    vram.evict("qwen")

    # Durum
    print(vram.status())
"""
import gc
import threading
import torch
from runtime.event_bus import Event, bus
from runtime.events import EventType


class VRAMManager:
    """
    Agresif GPU model yöneticisi.

    - Aynı anda sadece 1 model GPU'da kalır
    - Yeni model yüklenirken eskisi otomatik boşaltılır
    - Her boşaltmada torch.cuda.empty_cache() + gc.collect()
    - Thread-safe (GpuMutex ile korumalı)
    """

    def __init__(self, max_vram_mb: int = 4096):
        self._lock = threading.Lock()
        self._loaded: dict = {}          # model_id → model_obj
        self._current: str | None = None  # şu an GPU'da olan model
        self._max_vram_mb = max_vram_mb
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._total_mb = 0
        if self._device == "cuda":
            self._total_mb = torch.cuda.get_device_properties(0).total_memory / 1e6

    # ── Temel Özellikler ──

    @property
    def device(self) -> str:
        return self._device

    @property
    def available(self) -> bool:
        return self._device == "cuda"

    @property
    def memory_allocated_mb(self) -> float:
        if self._device == "cuda":
            return torch.cuda.memory_allocated() / 1e6
        return 0.0

    @property
    def memory_reserved_mb(self) -> float:
        if self._device == "cuda":
            return torch.cuda.memory_reserved() / 1e6
        return 0.0

    @property
    def memory_total_mb(self) -> float:
        return self._total_mb

    @property
    def memory_free_mb(self) -> float:
        return self._total_mb - self.memory_allocated_mb

    @property
    def current_model(self) -> str | None:
        return self._current

    # ── Model Yükleme / Boşaltma ──

    def load(self, model_id: str, load_fn):
        """
        Modeli yükle. Aynı ID zaten yüklüyse cached döndür.
        Farklı ID ise eskisini boşalt, yenisini yükle.

        Args:
            model_id: "qwen", "f5tts", "whisper" gibi tekil isim
            load_fn: Modeli oluşturan çağrılabilir (lambda/fonksiyon)

        Returns:
            Yüklenen model objesi
        """
        with self._lock:
            # Zaten bu model yüklüyse direkt döndür
            if self._current == model_id and model_id in self._loaded:
                return self._loaded[model_id]

            # Farklı model varsa boşalt
            if self._current and self._current != model_id:
                self._evict_locked(self._current)

            # Yükle
            if model_id not in self._loaded:
                bus.publish(Event(EventType.GPU_ALLOCATED, {
                    "action": "loading",
                    "model": model_id,
                    "memory_free_mb": self.memory_free_mb,
                }))
                try:
                    model = load_fn()
                    self._loaded[model_id] = model
                except Exception as e:
                    bus.publish(Event(EventType.SYSTEM_ERROR, {
                        "action": "model_load_failed",
                        "model": model_id,
                        "error": str(e),
                    }))
                    raise RuntimeError(f"VRAM: {model_id} yüklenemedi: {e}")

            self._current = model_id
            bus.publish(Event(EventType.GPU_ALLOCATED, {
                "action": "loaded",
                "model": model_id,
                "memory_allocated_mb": self.memory_allocated_mb,
                "memory_free_mb": self.memory_free_mb,
            }))
            return self._loaded[model_id]

    def evict(self, model_id: str):
        """Modeli GPU'dan zorla boşalt."""
        with self._lock:
            self._evict_locked(model_id)

    def evict_all(self):
        """Tüm modelleri boşalt."""
        with self._lock:
            for mid in list(self._loaded.keys()):
                self._evict_locked(mid)

    def _evict_locked(self, model_id: str):
        """Kilit altında model boşalt. _lock zaten alınmış olmalı."""
        if model_id not in self._loaded:
            return

        del self._loaded[model_id]
        if self._current == model_id:
            self._current = None

        if self._device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()

        bus.publish(Event(EventType.GPU_RELEASED, {
            "action": "evicted",
            "model": model_id,
            "memory_allocated_mb": self.memory_allocated_mb,
            "memory_free_mb": self.memory_free_mb,
        }))

    # ── Bağlam Yöneticisi (GpuMutex uyumlu) ──

    def acquire(self, model_id: str, load_fn):
        """
        Context manager olarak kullan:
            with vram.acquire("qwen", load_qwen) as model:
                result = model.generate(...)
            # bloktan çıkınca otomatik boşaltır
        """
        return _VRAMContext(self, model_id, load_fn)

    # ── Durum ──

    def status(self) -> dict:
        return {
            "device": self._device,
            "available": self.available,
            "current_model": self._current,
            "loaded_models": list(self._loaded.keys()),
            "memory_allocated_mb": round(self.memory_allocated_mb, 1),
            "memory_reserved_mb": round(self.memory_reserved_mb, 1),
            "memory_free_mb": round(self.memory_free_mb, 1),
            "memory_total_mb": round(self._total_mb, 1),
            "usage_pct": round(self.memory_allocated_mb / max(1, self._total_mb) * 100, 1),
        }


class _VRAMContext:
    """VRAM context manager: with vram.acquire(...) as model:"""

    def __init__(self, manager: VRAMManager, model_id: str, load_fn):
        self._mgr = manager
        self._id = model_id
        self._fn = load_fn
        self._model = None

    def __enter__(self):
        self._model = self._mgr.load(self._id, self._fn)
        return self._model

    def __exit__(self, *args):
        self._mgr.evict(self._id)
        self._model = None


# Global singleton
vram = VRAMManager(max_vram_mb=4096)
