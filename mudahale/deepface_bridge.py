"""
DeepFace Bridge — Yüz Tanıma ve Analiz.

Yetenekler:
- Yüz doğrulama (verify): 2 fotoğraf aynı kişi mi?
- Yüz analizi (analyze): yaş, cinsiyet, duygu, ırk
- Yüz bulma (find): veritabanında eşleşen yüz ara
- Yüz gömme (represent): yüz vektörü çıkar

VRAM Manager ile entegre — modeli yükler, işi bitince boşaltır.
"""
from pathlib import Path
from typing import Optional


class DeepFaceBridge:
    """DeepFace yüz tanıma motoru."""

    def __init__(self):
        self._ready = False
        self._check()

    def _check(self):
        try:
            import deepface
            self._ready = True
        except ImportError:
            self._ready = False

    def hazir_mi(self) -> bool:
        return self._ready

    def analyze(self, image_path: str, actions: list = None) -> dict:
        """
        Yüz analizi: yaş, cinsiyet, duygu, ırk.

        Args:
            image_path: Fotoğraf yolu
            actions: ['age', 'gender', 'emotion', 'race'] (hepsi default)
        """
        from deepface import DeepFace
        from altyapi.vram_manager import vram

        if actions is None:
            actions = ['age', 'gender', 'emotion', 'race']

        try:
            def _analyze():
                return DeepFace.analyze(
                    img_path=image_path,
                    actions=actions,
                    enforce_detection=False,
                    silent=True,
                )

            with vram.acquire("deepface", lambda: True):
                result = _analyze()
                vram.evict("deepface")

            # DeepFace returns list, tek yüz varsa ilkini al
            if isinstance(result, list) and len(result) > 0:
                result = result[0]

            return {"status": "ok", "data": result}
        except Exception as e:
            vram.evict("deepface")
            return {"status": "error", "message": str(e)[:300]}

    def verify(self, img1: str, img2: str) -> dict:
        """İki fotoğrafın aynı kişi olup olmadığını kontrol et."""
        from deepface import DeepFace
        from altyapi.vram_manager import vram

        try:
            with vram.acquire("deepface", lambda: True):
                result = DeepFace.verify(
                    img1_path=img1,
                    img2_path=img2,
                    enforce_detection=False,
                    silent=True,
                )
                vram.evict("deepface")

            return {
                "status": "ok",
                "verified": result.get("verified", False),
                "distance": result.get("distance", 0),
                "threshold": result.get("threshold", 0),
                "model": result.get("model", ""),
            }
        except Exception as e:
            vram.evict("deepface")
            return {"status": "error", "message": str(e)[:300]}

    def find(self, image_path: str, db_path: str) -> dict:
        """
        Veritabanında eşleşen yüz ara.

        Args:
            image_path: Aranacak fotoğraf
            db_path: Yüz veritabanı dizini
        """
        from deepface import DeepFace
        from altyapi.vram_manager import vram

        try:
            with vram.acquire("deepface", lambda: True):
                results = DeepFace.find(
                    img_path=image_path,
                    db_path=db_path,
                    enforce_detection=False,
                    silent=True,
                )
                vram.evict("deepface")

            # results: list of DataFrames, her model için bir tane
            matches = []
            for df in results:
                if not df.empty:
                    for _, row in df.head(5).iterrows():
                        matches.append({
                            "identity": row.get("identity", ""),
                            "distance": float(row.get("distance", 0)),
                        })

            return {"status": "ok", "matches": matches, "count": len(matches)}
        except Exception as e:
            vram.evict("deepface")
            return {"status": "error", "message": str(e)[:300]}

    def represent(self, image_path: str) -> dict:
        """Yüz embedding vektörü çıkar."""
        from deepface import DeepFace
        from altyapi.vram_manager import vram

        try:
            with vram.acquire("deepface", lambda: True):
                result = DeepFace.represent(
                    img_path=image_path,
                    enforce_detection=False,
                    silent=True,
                )
                vram.evict("deepface")

            if isinstance(result, list) and len(result) > 0:
                emb = result[0].get("embedding", [])
                return {
                    "status": "ok",
                    "embedding_size": len(emb),
                    "model": result[0].get("model", ""),
                }

            return {"status": "error", "message": "Yüz bulunamadı"}
        except Exception as e:
            vram.evict("deepface")
            return {"status": "error", "message": str(e)[:300]}


_deepface: Optional[DeepFaceBridge] = None

def get_deepface() -> DeepFaceBridge:
    global _deepface
    if _deepface is None:
        _deepface = DeepFaceBridge()
    return _deepface
