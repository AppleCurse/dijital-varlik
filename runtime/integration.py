"""
Entegrasyon Katmanı — Mevcut bridge'leri Runtime Kernel'a bağlar.

Eski agentik_dongu.py'deki tüm modüller, EventBus ve StateManager
üzerinden Kernel'a bağlanır. Mevcut kod bozulmaz, sadece sarılır.

Kullanım:
    from runtime.integration import IntegratedDongu
    dongu = IntegratedDongu()
    dongu.calistir("Merhaba, nasilsin?")
"""
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime import bus, state, Event, EventType, memory, gpu, health, kernel
from config.config import config


class IntegratedDongu:
    """
    Agentik Dongu'nun Runtime Kernel entegre versiyonu.

    Mevcut tüm bridge'leri kullanır ama:
    - Olayları EventBus'a publish eder
    - Durumu StateManager'da tutar
    - Sağlık kontrollerini HealthSupervisor'a kaydeder
    - GPU kullanımını GpuMutex ile korur
    """

    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.adim_sayisi = 0

        # ── Runtime altyapısını başlat ──
        self._wire_runtime()
        self._register_health_checks()
        self._connect_bridges()

        bus.publish(Event(EventType.SYSTEM_READY, {
            "session_id": self.session_id,
            "modules": list(self.__dict__.keys()),
        }))

    # ═══════════════════════════════════════════════════════════
    # ALTYAPI BAĞLANTISI
    # ═══════════════════════════════════════════════════════════

    def _wire_runtime(self):
        """Memory, GPU, Health bağlantılarını yap."""
        from altyapi.mem0_bridge import get_mem0
        from altyapi.letta_bridge import get_letta
        from altyapi.vram_manager import vram as vram_mgr

        self.mem0 = get_mem0()
        self.letta = get_letta()
        self.vram = vram_mgr
        memory.wire(mem0=self.mem0, letta=self.letta)

        # GPU durumunu state'e yaz
        state.update_gpu(
            allocated=False,
            device=gpu.device,
            memory_total_mb=gpu.memory_total_mb,
        )

    def _register_health_checks(self):
        """Tüm servislerin sağlık kontrollerini kaydet."""
        import requests

        def _check_litellm():
            try:
                r = requests.get(f"{config.LITELLM_URL}/models",
                                 headers={"Authorization": f"Bearer {config.LITELLM_KEY}"},
                                 timeout=5)
                return r.status_code == 200
            except Exception:
                return False

        def _check_browserless():
            try:
                r = requests.get(f"{config.BROWSERLESS_URL}/json/version", timeout=3)
                return r.status_code == 200
            except Exception:
                return False

        def _check_vram():
            try:
                return self.vram.memory_free_mb > 500  # en az 500MB serbest
            except Exception:
                return False

        self._check_litellm = _check_litellm
        self._check_browserless = _check_browserless
        health.register("litellm", _check_litellm)
        health.register("browserless", _check_browserless)
        health.register("vram", _check_vram)

    def _connect_bridges(self):
        """Mevcut bridge'leri yükle ve Kernel'a kaydet."""
        print("\n" + "=" * 50)
        print("  INTEGRATED DONGU — Runtime Kernel ile Başlatılıyor")
        print("=" * 50)

        # ── LLM ──
        from karar.mahkeme_engine import HakikatMahkemesi, LLMClient
        from altyapi.litellm_bridge import litellm
        self.llm = LLMClient(config.LITELLM_URL, config.LITELLM_KEY)
        self.litellm = litellm
        self.mahkeme = HakikatMahkemesi(llm=self.llm)

        litellm_ok = self.litellm.health()
        print(f"  LiteLLM  : {'OK' if litellm_ok else 'FAIL'}")
        state.update_service("litellm", ready=litellm_ok, status="ready" if litellm_ok else "error")

        # ── Beyin ──
        from karar.harness import get_harness
        self.harness = get_harness()
        print(f"  Mahkeme  : OK 4 rol")
        print(f"  Harness  : OK {len(self.harness.stratejiler)} strateji")
        state.update_service("mahkeme", ready=True, status="ready")
        state.update_service("harness", ready=True, status="ready")

        # ── Eller ──
        from karar.smolagents_bridge import get_smol
        from mudahale.web_tools import web_fetch, web_extract_title, web_screenshot, web_navigate
        from mudahale.browser_use_bridge import get_browser_use
        from mudahale.skyvern_bridge import get_skyvern
        from mudahale.atom_bridge import get_atom

        self.web_tools = [web_fetch, web_extract_title, web_screenshot, web_navigate]
        self.smol = get_smol(tools=self.web_tools)
        self.browser_use = get_browser_use()
        self.skyvern = get_skyvern()
        self.atom = get_atom()

        smol_ok = self.smol.hazir_mi()
        browser_ok = self.browser_use.hazir_mi()

        print(f"  smol     : {'OK' if smol_ok else 'FAIL'} - {len(self.web_tools)} arac")
        print(f"  Browser  : {'OK' if browser_ok else 'FAIL'} - CDP")
        print(f"  Skyvern  : {'OK' if self.skyvern.hazir_mi() else 'FAIL'}")
        print(f"  ATOM     : {'OK' if self.atom.hazir_mi() else 'FAIL'} + ChromaDB")

        state.update_service("smolagents", ready=smol_ok, status="ready" if smol_ok else "error")
        state.update_service("browser_use", ready=browser_ok, status="ready" if browser_ok else "error")
        state.update_service("skyvern", ready=self.skyvern.hazir_mi(), status="ready")
        state.update_service("atom", ready=self.atom.hazir_mi(), status="ready")

        # ── Duyular ──
        from mudahale.f5tts_bridge import get_f5tts
        from mudahale.qwen_bridge import get_qwen
        from mudahale.airi_bridge import get_airi
        from mudahale.pipecat_bridge import get_pipecat

        self.f5tts = get_f5tts()
        self.qwen = get_qwen()
        self.airi = get_airi()
        self.pipecat = get_pipecat()

        f5_ok = self.f5tts and self.f5tts.hazir_mi()
        qwen_ok = self.qwen and self.qwen.hazir_mi()

        print(f"  F5-TTS   : {'OK GPU' if f5_ok else 'FAIL'}")
        print(f"  Qwen-VL  : {'OK GPU' if qwen_ok else 'FAIL'}")
        print(f"  AIRI     : {'OK WebGPU' if self.airi and self.airi.hazir_mi() else 'FAIL'}")
        print(f"  Pipecat  : {'OK' if self.pipecat and self.pipecat.hazir_mi() else 'FAIL'}")

        state.update_service("f5tts", ready=f5_ok, status="ready" if f5_ok else "error")
        state.update_service("qwen_vl", ready=qwen_ok, status="ready" if qwen_ok else "error")

        # ── Kernel'a yetenekleri kaydet ──
        kernel.register_capability("litellm", "9router", health_fn=self._check_litellm)
        kernel.register_capability("browser_use", "browserless", health_fn=self._check_browserless)
        kernel.register_capability("qwen_vl", "qwen-vl", gpu_required=True)
        kernel.register_capability("f5tts", "f5-tts", gpu_required=True)
        kernel.register_capability("smolagents", "smolagents")
        kernel.register_capability("mahkeme", "mahkeme-engine")

        # ── Health monitor başlat ──
        health.start()

        print("=" * 50)
        print(f"  OTURUM: {self.session_id}")
        print("=" * 50 + "\n")

    # ═══════════════════════════════════════════════════════════
    # GÖREV ÇALIŞTIRMA (EventBus entegre)
    # ═══════════════════════════════════════════════════════════

    def calistir(self, gorev: str) -> Dict:
        """Görevi EventBus + mevcut mantık ile çalıştır."""
        self.adim_sayisi += 1
        baslangic = time.time()
        task_id = kernel.submit_task(gorev)

        state.update(active_task=gorev, current_text=gorev)
        bus.publish(Event(EventType.TASK_STARTED, {"task_id": task_id, "text": gorev[:120]}))

        print(f"\n{'='*60}")
        print(f"ADIM #{self.adim_sayisi}: {gorev[:120]}")
        print(f"{'='*60}")

        # ── FAZ 0: Bellek ──
        anilar = memory.search(gorev, scope="semantic", limit=5)
        print(f"\n[FAZ 0] BELLEK: {len(anilar)} ilgili ani")

        # ── FAZ 1: Mahkeme ──
        print(f"[FAZ 1] MAHKEME değerlendiriyor...")
        karar = self.mahkeme.yargila(claim=f"GOREV: {gorev}", mode="task")
        print(f"  Karar: {karar.verdict.value} (%{karar.confidence*100:.0f})")

        bus.publish(Event(
            EventType.TASK_APPROVED if karar.verdict.value == "APPROVED" else EventType.TASK_REJECTED,
            {"task_id": task_id, "verdict": karar.verdict.value, "confidence": karar.confidence}
        ))

        if karar.verdict.value == "REJECTED":
            sonuc = {"status": "rejected", "message": str(karar.judge_reasoning)[:300]}
            bus.publish(Event(EventType.TASK_COMPLETED, {"task_id": task_id, "result": sonuc}))
            return sonuc

        # ── FAZ 2: Rota ──
        from agentik_dongu import gorev_tipini_belirle, GorevTipi
        tip = gorev_tipini_belirle(gorev)
        print(f"[FAZ 2] ROTA: {tip.value}")

        # ── FAZ 3: İcra ──
        print(f"[FAZ 3] ICRA...")
        try:
            if tip == GorevTipi.WEB and self.browser_use.hazir_mi():
                sonuc_metni = self.browser_use.calistir(gorev)
                bus.publish(Event(EventType.BROWSER_COMPLETED, {"task_id": task_id}))
            else:
                sonuc_metni = self.smol.calistir(gorev)
                bus.publish(Event(EventType.TOOL_COMPLETED, {"task_id": task_id, "tool": "smolagents"}))

            if isinstance(sonuc_metni, dict):
                sonuc_metni = sonuc_metni.get("message", str(sonuc_metni))
            if sonuc_metni is None:
                sonuc_metni = "Boş sonuç"

            durum = "success"
        except Exception as e:
            sonuc_metni = str(e)[:500]
            durum = "error"
            bus.publish(Event(EventType.TASK_FAILED, {"task_id": task_id, "error": str(e)[:200]}))
            traceback.print_exc()

        icra_sonucu = {"status": durum, "message": str(sonuc_metni)[:500]}

        # ── FAZ 4: Kayıt ──
        memory.store(f"[{tip.value}] {gorev[:100]} → {durum}", scope="semantic")
        memory.session_update(self.session_id, {"adim": self.adim_sayisi, "durum": durum})

        # ── State güncelle ──
        sure = time.time() - baslangic
        state.update(task_count=state.snapshot.task_count + 1,
                     active_task=None,
                     current_text=None)

        if durum == "error":
            state.update(error_count=state.snapshot.error_count + 1)

        bus.publish(Event(EventType.TASK_COMPLETED, {
            "task_id": task_id,
            "status": durum,
            "duration_s": sure,
        }))

        print(f"\n{'─'*60}")
        print(f"TAMAMLANDI ({sure:.1f}s) - {durum}")
        print(f"{'─'*60}")

        return icra_sonucu

    # ═══════════════════════════════════════════════════════════
    # TOPLU TEST
    # ═══════════════════════════════════════════════════════════

    def toplu_test(self):
        """3 test görevini çalıştır."""
        print(f"\n{'='*60}")
        print("TOPLU SISTEM TESTI (Runtime Kernel)")
        print(f"{'='*60}")

        testler = [
            ("Soru", "Merhaba, nasilsin?"),
            ("Web", "https://example.com sitesinin basligini getir"),
            ("Analiz", "Su an saat kac? Tarihi soyle"),
        ]

        sonuclar = {}
        for etiket, gorev in testler:
            print(f"\n{'─'*40}")
            print(f"TEST: {etiket}")
            print(f"{'─'*40}")
            try:
                sonuclar[etiket] = self.calistir(gorev)
            except Exception as e:
                sonuclar[etiket] = {"status": "crash", "message": str(e)}
                traceback.print_exc()

        print(f"\n{'='*60}")
        print("TEST OZETI")
        print(f"{'='*60}")
        for etiket, s in sonuclar.items():
            durum = s.get("status", "?")
            icon = "OK" if durum == "success" else "FAIL"
            print(f"  {icon} {etiket}: {durum}")

        return sonuclar

    # ═══════════════════════════════════════════════════════════

    def durum(self):
        """Sistem durum raporu."""
        return {
            "oturum": self.session_id,
            "adim": self.adim_sayisi,
            "runtime": {
                "eventbus_listeners": bus.listener_count,
                "event_history": len(bus.history),
                "services": health.report,
                "gpu": gpu.status(),
            },
            "state": {
                "task_count": state.snapshot.task_count,
                "error_count": state.snapshot.error_count,
                "active_task": state.snapshot.active_task,
            },
            "vram": self.vram.status(),
        }

    def kapat(self):
        """Sistemi kapat."""
        health.stop()
        self.vram.evict_all()
        memory.session_end(self.session_id)
        bus.publish(Event(EventType.SYSTEM_STOPPING, {"session_id": self.session_id}))
        print("Integrated Dongu kapandi.")
