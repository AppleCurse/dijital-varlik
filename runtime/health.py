"""
HealthSupervisor — Servis Sağlık İzleyicisi.

Her servis için kalp atışı, gecikme, hata sayısı takip eder.
Sağlık durumu değişince EventBus'a bildirir.

Kullanım:
    from runtime.health import health

    health.register("litellm", check_fn=lambda: requests.get("...").ok)
    health.start()  # arka planda periyodik kontrol
"""
import time
import threading
from typing import Callable, Dict, Optional
from dataclasses import dataclass, field
from runtime.events import EventType
from runtime.event_bus import Event, bus


@dataclass
class HealthRecord:
    name: str
    check_fn: Optional[Callable[[], bool]] = None
    ready: bool = False
    last_ok: float = 0.0
    last_check: float = 0.0
    latency_ms: float = 0.0
    error_count: int = 0
    consecutive_failures: int = 0
    restart_count: int = 0
    status: str = "uninitialized"  # ready, busy, error, recovering, offline


class HealthSupervisor:
    """Periyodik sağlık kontrolü yapan gözlemci."""

    def __init__(self, interval: float = 15.0):
        self._services: Dict[str, HealthRecord] = {}
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def register(self, name: str, check_fn: Callable[[], bool]):
        """İzlenecek servisi kaydet."""
        self._services[name] = HealthRecord(name=name, check_fn=check_fn, status="ready")

    def unregister(self, name: str):
        self._services.pop(name, None)

    def start(self):
        """Arka planda periyodik kontrolü başlat."""
        if self._running:
            return
        self._running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(self._interval):
            self.check_all()

    def check_all(self) -> Dict[str, bool]:
        """Tüm servisleri kontrol et, durum haritası döndür."""
        results = {}
        for name, rec in self._services.items():
            results[name] = self._check_one(rec)
        bus.publish(Event(EventType.HEALTH_CHECK, {"results": results}))
        return results

    def _check_one(self, rec: HealthRecord) -> bool:
        if not rec.check_fn:
            return rec.ready

        rec.last_check = time.time()
        old_status = rec.status

        try:
            t0 = time.time()
            ok = rec.check_fn()
            rec.latency_ms = (time.time() - t0) * 1000
        except Exception:
            ok = False
            rec.latency_ms = 0

        if ok:
            rec.ready = True
            rec.last_ok = time.time()
            rec.consecutive_failures = 0
            if old_status in ("error", "recovering"):
                rec.status = "recovering"
                bus.publish(Event(EventType.HEALTH_RECOVERED, {"service": rec.name}))
            else:
                rec.status = "ready"
        else:
            rec.error_count += 1
            rec.consecutive_failures += 1
            rec.ready = False
            if rec.consecutive_failures >= 3:
                rec.status = "error"
                bus.publish(Event(EventType.HEALTH_DEGRADED, {
                    "service": rec.name,
                    "consecutive_failures": rec.consecutive_failures,
                }))

        if old_status != rec.status:
            bus.publish(Event(EventType.HEALTH_CHANGED, {
                "service": rec.name,
                "from": old_status,
                "to": rec.status,
            }))

        return ok

    @property
    def report(self) -> Dict:
        """Anlık sağlık raporu."""
        return {
            name: {
                "ready": rec.ready,
                "status": rec.status,
                "latency_ms": rec.latency_ms,
                "error_count": rec.error_count,
                "restart_count": rec.restart_count,
            }
            for name, rec in self._services.items()
        }

    @property
    def all_healthy(self) -> bool:
        return all(rec.ready for rec in self._services.values())


# Global singleton
health = HealthSupervisor(interval=15.0)
