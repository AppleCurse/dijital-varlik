"""
EventBus — Merkezi Olay Yolu.

Tüm modüller arası iletişim buradan geçer.
Publish/Subscribe pattern. Modüller birbirini tanımaz.

Kullanım:
    from runtime import bus, EventType

    # Yayınla
    bus.publish(Event(EventType.TASK_COMPLETED, {"task_id": "x", "result": "ok"}))

    # Dinle
    @bus.on(EventType.TASK_COMPLETED)
    def handle(event):
        print(event.data)
"""
import time
import uuid
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from runtime.events import EventType


@dataclass
class Event:
    """Sistemde taşınan olay."""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    correlation_id: Optional[str] = None

    def __repr__(self):
        data_preview = str(self.data)[:80]
        return f"Event({self.type.value}, id={self.id}, data={data_preview})"


class EventBus:
    """
    Merkezi olay yolu. Thread-safe.

    - publish(event): Olayı tüm dinleyicilere ilet
    - subscribe(event_type, callback): Dinleyici kaydet
    - on(event_type): Dekoratör olarak kullan
    """

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._wildcard_listeners: List[Callable] = []
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._max_history = 200

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Belirli bir olay tipine dinleyici ekle."""
        with self._lock:
            self._listeners[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[Event], None]):
        """Tüm olayları dinle (wildcard)."""
        with self._lock:
            self._wildcard_listeners.append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Dinleyiciyi kaldır."""
        with self._lock:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)

    def on(self, event_type: EventType):
        """Dekoratör: @bus.on(EventType.TASK_COMPLETED)"""
        def decorator(func: Callable[[Event], None]):
            self.subscribe(event_type, func)
            return func
        return decorator

    def publish(self, event: Event):
        """Olayı tüm kayıtlı dinleyicilere ilet."""
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            listeners = list(self._listeners.get(event.type, []))
            wildcards = list(self._wildcard_listeners)

        # Kilit dışında çağır (deadlock önleme)
        for cb in listeners:
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Listener error for {event.type.value}: {e}")

        for cb in wildcards:
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Wildcard error: {e}")

    @property
    def history(self) -> List[Event]:
        """Son olayların listesi (gözlemlenebilirlik için)."""
        with self._lock:
            return list(self._history)

    @property
    def listener_count(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._listeners.values()) + len(self._wildcard_listeners)


# Global singleton
bus = EventBus()
