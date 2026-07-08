"""
Olay Tipi Sabitleri — Sistemdeki tüm olaylar burada tanımlanır.

Her olay `domain.eylem` formatındadır.
Modüller sadece bu sabitlerle publish/subscribe yapar.
"""
from enum import Enum


class EventType(str, Enum):
    # ── Yaşam Döngüsü ──
    SYSTEM_STARTING = "system.starting"
    SYSTEM_READY = "system.ready"
    SYSTEM_STOPPING = "system.stopping"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"

    # ── Görev ──
    TASK_CREATED = "task.created"
    TASK_APPROVED = "task.approved"
    TASK_REJECTED = "task.rejected"
    TASK_ROUTED = "task.routed"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # ── Plan ──
    PLAN_CREATED = "plan.created"
    PLAN_STEP_STARTED = "plan.step_started"
    PLAN_STEP_COMPLETED = "plan.step_completed"
    PLAN_COMPLETED = "plan.completed"

    # ── Görü ──
    VISION_IMAGE_CAPTURED = "vision.image_captured"
    VISION_ANALYSIS_STARTED = "vision.analysis_started"
    VISION_ANALYSIS_COMPLETED = "vision.analysis_completed"
    VISION_ERROR = "vision.error"

    # ── Ses ──
    SPEECH_RECOGNIZED = "speech.recognized"
    SPEECH_SYNTHESIS_STARTED = "speech.synthesis_started"
    SPEECH_SYNTHESIS_COMPLETED = "speech.synthesis_completed"
    SPEECH_ERROR = "speech.error"

    # ── Tarayıcı ──
    BROWSER_STARTED = "browser.started"
    BROWSER_NAVIGATED = "browser.navigated"
    BROWSER_CONTENT_EXTRACTED = "browser.content_extracted"
    BROWSER_COMPLETED = "browser.completed"
    BROWSER_ERROR = "browser.error"

    # ── Araç ──
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_ERROR = "tool.error"

    # ── Bellek ──
    MEMORY_SEARCHED = "memory.searched"
    MEMORY_STORED = "memory.stored"
    MEMORY_UPDATED = "memory.updated"

    # ── GPU ──
    GPU_ALLOCATED = "gpu.allocated"
    GPU_RELEASED = "gpu.released"
    GPU_MEMORY_LOW = "gpu.memory_low"

    # ── Sağlık ──
    HEALTH_CHECK = "health.check"
    HEALTH_CHANGED = "health.changed"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"

    # ── Mahkeme ──
    COURT_VERDICT = "court.verdict"
    COURT_DISSENT = "court.dissent"
