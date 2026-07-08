"""
GpuMutex — Tek GPU için basit kilit mekanizması.

GTX 1650 (4.3 GB) için yeterli. Kuyruk, priority, timeout yok.
Sadece acquire/release. Thread-safe.

Kullanım:
    from runtime.gpu import gpu

    with gpu:
        model.to("cuda")
        result = model(image)
"""
import threading
import torch
from runtime.events import EventType
from runtime.event_bus import Event, bus


class GpuMutex:
    """Tek GPU için context manager tabanlı kilit."""

    def __init__(self):
        self._lock = threading.Lock()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._total_mb = 0
        if self._device == "cuda":
            self._total_mb = torch.cuda.get_device_properties(0).total_memory / 1e6

    @property
    def device(self) -> str:
        return self._device

    @property
    def available(self) -> bool:
        return self._device == "cuda"

    @property
    def memory_used_mb(self) -> float:
        if self._device == "cuda":
            return torch.cuda.memory_allocated() / 1e6
        return 0.0

    @property
    def memory_total_mb(self) -> float:
        return self._total_mb

    @property
    def locked(self) -> bool:
        return self._lock.locked()

    def __enter__(self):
        self._lock.acquire()
        bus.publish(Event(EventType.GPU_ALLOCATED, {
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self._total_mb,
        }))
        return self

    def __exit__(self, *args):
        bus.publish(Event(EventType.GPU_RELEASED, {
            "memory_used_mb": self.memory_used_mb,
        }))
        self._lock.release()

    def status(self) -> dict:
        return {
            "device": self._device,
            "available": self.available,
            "memory_used_mb": self.memory_used_mb,
            "memory_total_mb": self._total_mb,
            "locked": self.locked,
        }


# Global singleton
gpu = GpuMutex()
