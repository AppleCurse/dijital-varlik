"""
Qwen-VL Bridge — Görüntü Anlama (Kamera/Ekran)
GPU (CUDA 12.x) GEREKIR. INT4 nicemleme ile 4GB VRAM'e sığar.
VRAM Manager ile entegre: model yüklemede öncekini boşaltır.
"""
from typing import Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QWEN_DIR = ROOT / "Qwen3-VL-main"


class QwenVLBridge:
    """Qwen-VL görme modeli köprüsü. INT4 nicemlemeli, VRAM dostu."""

    def __init__(self):
        self._ready = QWEN_DIR.exists()
        self._gpu_available = self._check_gpu()
        self._model = None
        self._processor = None

    def _check_gpu(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def hazir_mi(self) -> bool:
        return self._ready and self._gpu_available

    def _load_model(self):
        """Modeli INT4 nicemleme ile yükle. VRAM Manager üzerinden."""
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-VL-7B-Instruct",
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        self._processor = AutoProcessor.from_pretrained(
            "Qwen/Qwen2.5-VL-7B-Instruct",
            trust_remote_code=True,
        )

    def calistir(self, gorev: str, image_path: str = None) -> dict:
        """Görüntü analizi yap. VRAM Manager üzerinden model yükler."""
        if not self._gpu_available:
            return {"status": "error",
                    "message": "Qwen-VL GPU bekliyor."}

        try:
            from altyapi.vram_manager import vram

            # VRAM Manager: önceki modeli boşalt, Qwen'i yükle
            if self._model is None:
                vram.load("qwen", self._load_model)

            if image_path is None:
                return {"status": "ok",
                        "message": "Qwen-VL INT4 GPU hazir. Goruntu yolu gerekli."}

            # Görüntü analizi
            from PIL import Image
            image = Image.open(image_path)
            inputs = self._processor(text=gorev, images=image,
                                     return_tensors="pt").to("cuda")
            with torch.no_grad():
                output = self._model.generate(**inputs, max_new_tokens=256)
            result = self._processor.decode(output[0], skip_special_tokens=True)

            return {"status": "ok", "message": result}

        except Exception as e:
            return {"status": "error", "message": str(e)[:500]}

    def unload(self):
        """Modeli VRAM'den boşalt."""
        if self._model is not None:
            from altyapi.vram_manager import vram
            vram.evict("qwen")
            self._model = None
            self._processor = None


_qwen: Optional[QwenVLBridge] = None

def get_qwen() -> QwenVLBridge:
    global _qwen
    if _qwen is None:
        _qwen = QwenVLBridge()
    return _qwen
