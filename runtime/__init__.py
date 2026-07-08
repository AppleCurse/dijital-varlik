"""
Runtime Kernel — Dijital Varlik'in merkezi sinir sistemi.

Tüm modüller bu paket üzerinden haberleşir.
Hiçbir modül birbirini doğrudan çağırmaz.
"""
from runtime.event_bus import EventBus, Event, bus
from runtime.state_manager import StateManager, SystemState, state
from runtime.events import EventType
from runtime.memory import UnifiedMemory, memory
from runtime.gpu import GpuMutex, gpu
from runtime.health import HealthSupervisor, health
from runtime.kernel import RuntimeKernel, kernel
from runtime.integration import IntegratedDongu

__all__ = [
    "EventBus", "Event", "bus",
    "StateManager", "SystemState", "state",
    "EventType",
    "UnifiedMemory", "memory",
    "GpuMutex", "gpu",
    "HealthSupervisor", "health",
    "RuntimeKernel", "kernel",
    "IntegratedDongu",
]
