"""
RuntimeKernel — Dijital Varlik'in Merkezi Sinir Sistemi.

Tüm modüller buradan yönetilir. Hiçbir şey Kernel'ı bypass etmez.

Sorumluluklar:
- Başlangıç / kapanış sırası
- Bağımlılık enjeksiyonu
- Yaşam döngüsü yönetimi
- Görev yönlendirme
- Olay dağıtımı
- GPU zamanlaması
- Sağlık izleme
- Kurtarma
"""
import time
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from runtime.event_bus import EventBus, Event, bus
from runtime.state_manager import StateManager, SystemState, state, ServiceStatus
from runtime.events import EventType


class ModuleLifecycle:
    """Bir modülün yaşam döngüsü durumları."""
    UNINITIALIZED = "uninitialized"
    INIT = "init"
    READY = "ready"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    RECOVERING = "recovering"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class RegisteredCapability:
    """Runtime'a kayıtlı bir yetenek."""
    name: str
    provider: str
    version: str = "1.0.0"
    status: str = ModuleLifecycle.UNINITIALIZED
    gpu_required: bool = False
    priority: int = 5
    health_fn: Optional[Callable[[], bool]] = None
    init_fn: Optional[Callable[[], bool]] = None
    shutdown_fn: Optional[Callable[[], None]] = None


class RuntimeKernel:
    """
    Merkezi orkestratör.

    Kullanım:
        kernel = RuntimeKernel()
        kernel.register_capability("vision", "qwen-vl", gpu_required=True, ...)
        kernel.start()
        kernel.submit_task("Merhaba, nasılsın?")
        kernel.stop()
    """

    def __init__(self):
        self._capabilities: Dict[str, RegisteredCapability] = {}
        self._started = False
        self._lock = threading.RLock()
        self._health_thread: Optional[threading.Thread] = None
        self._health_interval = 15.0
        self._stop_health = threading.Event()

        # EventBus'a bağlan
        self._setup_listeners()

    # ── Yetenek Kaydı ──

    def register_capability(
        self,
        name: str,
        provider: str,
        version: str = "1.0.0",
        gpu_required: bool = False,
        priority: int = 5,
        health_fn: Optional[Callable[[], bool]] = None,
        init_fn: Optional[Callable[[], bool]] = None,
        shutdown_fn: Optional[Callable[[], None]] = None,
    ):
        """Runtime'a bir yetenek kaydet."""
        with self._lock:
            cap = RegisteredCapability(
                name=name,
                provider=provider,
                version=version,
                gpu_required=gpu_required,
                priority=priority,
                health_fn=health_fn,
                init_fn=init_fn,
                shutdown_fn=shutdown_fn,
            )
            self._capabilities[name] = cap
            state.update_service(name)

        bus.publish(Event(EventType.SYSTEM_STARTING,
                          {"action": "capability_registered", "capability": name}))
        return cap

    @property
    def capabilities(self) -> Dict[str, RegisteredCapability]:
        return dict(self._capabilities)

    # ── Yaşam Döngüsü ──

    def start(self) -> bool:
        """Tüm sistemi başlat."""
        if self._started:
            return True

        bus.publish(Event(EventType.SYSTEM_STARTING, {"phase": "kernel_start"}))
        print("\n" + "=" * 60)
        print("  RUNTIME KERNEL — Dijital Varlik Başlatılıyor")
        print("=" * 60)

        state.update(uptime_seconds=0.0)

        # Bağımlılık sırasına göre başlat
        boot_order = ["litellm", "mem0", "letta", "smolagents",
                      "browser_use", "pipecat", "f5tts", "qwen_vl"]

        for name in boot_order:
            cap = self._capabilities.get(name)
            if not cap:
                continue
            self._init_capability(cap)

        # Health monitor başlat
        self._stop_health.clear()
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()

        self._started = True
        state.update(uptime_seconds=time.time())
        bus.publish(Event(EventType.SYSTEM_READY, {"boot_order": boot_order}))

        print("=" * 60)
        print("  RUNTIME KERNEL — Hazır")
        print("=" * 60 + "\n")
        return True

    def stop(self):
        """Sistemi kontrollü kapat."""
        bus.publish(Event(EventType.SYSTEM_STOPPING, {}))
        self._stop_health.set()

        for name, cap in reversed(list(self._capabilities.items())):
            if cap.shutdown_fn:
                try:
                    cap.shutdown_fn()
                except Exception as e:
                    print(f"[Kernel] {name} kapatma hatası: {e}")

        self._started = False
        bus.publish(Event(EventType.SYSTEM_STOPPED, {}))
        print("Runtime Kernel kapandı.")

    def _init_capability(self, cap: RegisteredCapability):
        """Bir yeteneği başlat."""
        name = cap.name
        print(f"  [{name}] başlatılıyor...", end=" ")
        state.update_service(name, status=ModuleLifecycle.INIT)

        if cap.init_fn:
            try:
                ok = cap.init_fn()
            except Exception as e:
                print(f"HATA: {e}")
                state.update_service(name, status=ModuleLifecycle.ERROR, error=str(e))
                return
        else:
            ok = True

        if ok:
            state.update_service(name, status=ModuleLifecycle.READY, ready=True,
                                 last_heartbeat=time.time())
            print("OK")
        else:
            state.update_service(name, status=ModuleLifecycle.ERROR,
                                 error="init_fn returned False")
            print("FAIL")

    # ── Sağlık İzleme ──

    def _health_loop(self):
        """Periyodik sağlık kontrolü."""
        while not self._stop_health.wait(self._health_interval):
            self._run_health_checks()

    def _run_health_checks(self):
        """Tüm servisleri kontrol et."""
        for name, cap in self._capabilities.items():
            if not cap.health_fn:
                continue
            try:
                t0 = time.time()
                ok = cap.health_fn()
                latency = (time.time() - t0) * 1000
                status = ModuleLifecycle.READY if ok else ModuleLifecycle.ERROR
                state.update_service(name, status=status, ready=ok,
                                     last_heartbeat=time.time(), latency_ms=latency)
            except Exception as e:
                state.update_service(name, status=ModuleLifecycle.ERROR, error=str(e))

        bus.publish(Event(EventType.HEALTH_CHECK, {
            "services": {
                name: {"ready": s.ready, "error": s.error}
                for name, s in state.snapshot.services.items()
            }
        }))

    @property
    def health_report(self) -> Dict[str, Any]:
        """Anlık sağlık raporu."""
        s = state.snapshot
        return {
            "uptime": s.uptime_seconds,
            "services": {
                name: {"ready": svc.ready, "busy": svc.busy, "error": svc.error,
                       "latency_ms": svc.latency_ms, "restarts": svc.restart_count}
                for name, svc in s.services.items()
            },
            "gpu": {
                "allocated": s.gpu_status.allocated,
                "memory_used_mb": s.gpu_status.memory_used_mb,
            },
            "tasks": {"total": s.task_count, "errors": s.error_count},
        }

    # ── Görev Gönderimi ──

    def submit_task(self, task_text: str, priority: int = 5) -> str:
        """Görevi işleme kuyruğuna al, task_id döndür."""
        import uuid
        task_id = str(uuid.uuid4())[:8]

        bus.publish(Event(EventType.TASK_CREATED, {
            "task_id": task_id,
            "text": task_text,
            "priority": priority,
        }))
        return task_id

    # ── Olay Dinleyicileri ──

    def _setup_listeners(self):
        """Kernel'in dinlediği sistem olayları."""

        @bus.on(EventType.TASK_COMPLETED)
        def _on_task_done(event: Event):
            state.update(task_count=state.snapshot.task_count + 1)

        @bus.on(EventType.TASK_FAILED)
        def _on_task_fail(event: Event):
            s = state.snapshot
            state.update(task_count=s.task_count + 1, error_count=s.error_count + 1)

        @bus.on(EventType.HEALTH_DEGRADED)
        def _on_health_degraded(event: Event):
            svc = event.data.get("service", "?")
            print(f"[Kernel] ⚠️ Sağlık azaldı: {svc} — {event.data.get('error', '')}")


# Global singleton
kernel = RuntimeKernel()
