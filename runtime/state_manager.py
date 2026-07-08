"""
StateManager — Paylaşımlı Değişmez Sistem Durumu.

Tek kaynak. Tüm modüller buradan okur, buraya yazar.
Thread-safe, copy-on-write.

Kullanım:
    from runtime import state

    # Oku
    gorev = state.snapshot.active_task

    # Güncelle (immutable — yeni obje döner)
    state.update(active_task="yeni gorev")
"""
import threading
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional
from runtime.events import EventType
from runtime.event_bus import Event, bus


@dataclass(frozen=True)
class GPUStatus:
    allocated: bool = False
    device: str = ""
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    queue_depth: int = 0


@dataclass(frozen=True)
class ServiceStatus:
    name: str
    status: str = "uninitialized"
    ready: bool = False
    busy: bool = False
    error: Optional[str] = None
    last_heartbeat: float = 0.0
    latency_ms: float = 0.0
    restart_count: int = 0


@dataclass(frozen=True)
class SystemState:
    """Değişmez sistem durumu. Her güncelleme yeni bir obje oluşturur."""

    # Konuşma
    conversation_id: str = ""
    active_task: Optional[str] = None
    active_plan: Optional[Dict] = None

    # Duyusal
    current_image: Optional[str] = None       # base64 ya da dosya yolu
    current_audio: Optional[str] = None       # dosya yolu
    current_text: Optional[str] = None        # STT çıktısı

    # Tarayıcı
    current_browser_session: Optional[str] = None
    current_url: Optional[str] = None

    # GPU
    gpu_status: GPUStatus = field(default_factory=GPUStatus)

    # Servis durumları
    services: Dict[str, ServiceStatus] = field(default_factory=dict)

    # Bellek bağlamı
    memory_context: List[Dict] = field(default_factory=list)

    # İstatistik
    task_count: int = 0
    error_count: int = 0
    uptime_seconds: float = 0.0


class StateManager:
    """
    Paylaşımlı durum yöneticisi. Thread-safe.

    Güncellemeler atomiktir. Her değişiklik olay olarak yayınlanır.
    """

    def __init__(self):
        self._state: SystemState = SystemState()
        self._lock = threading.RLock()
        self._observers: List[callable] = []

    @property
    def snapshot(self) -> SystemState:
        """Mevcut durumun değişmez kopyasını döndür."""
        with self._lock:
            return self._state

    def update(self, **kwargs) -> SystemState:
        """
        Durumu atomik güncelle. Yeni state döner.

        Örnek: state.update(active_task="gorev_123", current_text="merhaba")
        """
        with self._lock:
            old = self._state
            new = replace(old, **kwargs)
            self._state = new
            self._notify(old, new)
            return new

    def update_gpu(self, **kwargs) -> SystemState:
        """GPU alt durumunu güncelle."""
        with self._lock:
            old = self._state
            new_gpu = replace(old.gpu_status, **kwargs)
            new = replace(old, gpu_status=new_gpu)
            self._state = new
            self._notify(old, new)
            return new

    def update_service(self, name: str, **kwargs) -> SystemState:
        """Bir servisin durumunu güncelle."""
        with self._lock:
            old = self._state
            services = dict(old.services)
            existing = services.get(name, ServiceStatus(name=name))
            services[name] = replace(existing, **kwargs)
            new = replace(old, services=services)
            self._state = new
            self._notify(old, new)
            return new

    def observe(self, callback: callable):
        """Durum değişikliklerini dinle."""
        self._observers.append(callback)

    def _notify(self, old: SystemState, new: SystemState):
        for cb in self._observers:
            try:
                cb(old, new)
            except Exception:
                pass

    @property
    def is_ready(self) -> bool:
        """Tüm kritik servisler hazır mı?"""
        s = self.snapshot
        critical = ["litellm", "browser_use", "smolagents"]
        return all(
            s.services.get(name, ServiceStatus(name=name)).ready
            for name in critical
        )


# Global singleton
state = StateManager()
