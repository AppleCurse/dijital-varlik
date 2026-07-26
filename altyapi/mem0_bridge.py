"""
Mem0 Bridge - Hafiza Yonetimi
JSONL tabanli hafif depolama
"""

import os
import json
from datetime import datetime
from typing import Any, List, Optional, Dict
from pathlib import Path


class Mem0Bridge:
    """
    Mem0 alternatifi - JSONL dosyasi uzerinde calisan hafiza sistemi.
    Aspasia'nin uzun vadeli bellek ihtiyaclarini karsilar.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            # Config klasorune goreli yol
            base_dir = Path(__file__).parent.parent
            storage_path = base_dir / "bellek" / "memory_store.jsonl"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosya yoksa olustur
        if not self.storage_path.exists():
            self.storage_path.touch()
    
    def kaydet(self, anahtar: str, deger: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Bir aniyi/bilgiyi kaydet.
        
        Args:
            anahtar: Bilginin anahtari
            deger: Kaydedilecek deger
            metadata: Ek meta veriler
            
        Returns:
            Basari durumu
        """
        try:
            kayit = {
                "type": "memory",
                "key": anahtar,
                "value": deger,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(kayit, ensure_ascii=False) + '\n')
            
            return True
        except Exception as e:
            print(f"Mem0 kaydet hatasi: {e}")
            return False
    
    def hatirla(self, anahtar: str, limit: int = 10) -> List[Dict]:
        """
        Anahtara gore anilari getir.
        
        Args:
            anahtar: Arama anahtari (kismi eslesme)
            limit: Maksimum sonuc sayisi
            
        Returns:
            Anilar listesi
        """
        sonuclar = []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for satir in f:
                    satir = satir.strip()
                    if not satir:
                        continue
                    
                    try:
                        kayit = json.loads(satir)
                        if kayit.get('type') == 'memory':
                            key = kayit.get('key', '')
                            if anahtar.lower() in key.lower():
                                sonuclar.append(kayit)
                                if len(sonuclar) >= limit:
                                    break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return sonuclar
    
    def olay_kaydet(self, olay_tipi: str, veri: Dict) -> bool:
        """
        Bir olayi kaydet (konversasyon, sistem eventi vb.)
        
        Args:
            olay_tipi: Olay tipi (conversation, system, error vb.)
            veri: Olay verileri
            
        Returns:
            Basari durumu
        """
        try:
            kayit = {
                "type": "event",
                "event_type": olay_tipi,
                "data": veri,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(kayit, ensure_ascii=False) + '\n')
            
            return True
        except Exception as e:
            print(f"Mem0 olay_kaydet hatasi: {e}")
            return False
    
    def sorgula(self, tip: str = "memory", event_type: Optional[str] = None) -> List[Dict]:
        """
        Tip veya event type'a gore tum kayitlari getir.
        
        Args:
            tip: Kayit tipi (memory, event)
            event_type: Event tipi (sadece event'ler icin)
            
        Returns:
            Kayit listesi
        """
        sonuclar = []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for satir in f:
                    satir = satir.strip()
                    if not satir:
                        continue
                    
                    try:
                        kayit = json.loads(satir)
                        if kayit.get('type') == tip:
                            if event_type is None or kayit.get('event_type') == event_type:
                                sonuclar.append(kayit)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return sonuclar
    
    def temizle(self) -> bool:
        """Tum kayitlari temizle"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                pass  # Dosyayi bosalt
            return True
        except Exception as e:
            print(f"Mem0 temizle hatasi: {e}")
            return False
    
    def istatistik(self) -> Dict:
        """Hafiza istatistiklerini dondur"""
        memory_count = 0
        event_count = 0
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for satir in f:
                    satir = satir.strip()
                    if not satir:
                        continue
                    
                    try:
                        kayit = json.loads(satir)
                        if kayit.get('type') == 'memory':
                            memory_count += 1
                        elif kayit.get('type') == 'event':
                            event_count += 1
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return {
            "memory_count": memory_count,
            "event_count": event_count,
            "total": memory_count + event_count,
            "storage_path": str(self.storage_path)
        }


# Singleton instance
_mem0_instance: Optional[Mem0Bridge] = None

def get_mem0() -> Mem0Bridge:
    """Mem0 instance'ini al veya olustur"""
    global _mem0_instance
    if _mem0_instance is None:
        _mem0_instance = Mem0Bridge()
    return _mem0_instance
