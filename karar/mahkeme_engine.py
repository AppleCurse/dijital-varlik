"""
Mahkeme Engine - Karar Mekanizmasi
Aspasia'nin stratejik dusunce ve karar verme sistemi
4 rol: Savci, Mudafii, Hakim, Juri
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class HakikatMahkemesi:
    """
    Aspasia'nin ic kararlilik mekanizmasi.
    Her onemli karari 4 rolu degerlendirerek alir.
    """
    
    def __init__(self):
        self.roller = {
            'savci': self._savci_degerlendir,
            'mudafii': self._mudafii_degerlendir,
            'hakim': self._hakim_degerlendir,
            'juri': self._juri_degerlendir
        }
        
        self.son_karar: Optional[Dict] = None
    
    def degerlendir(self, durum: str, baglam: Optional[Dict] = None) -> Dict:
        """
        Bir durumu 4 rolu kullanarak degerlendir.
        
        Args:
            durum: Degerlendirilecek durum/mesaj
            baglam: Ek baglam bilgisi
            
        Returns:
            Karar sonucu
        """
        gorusler = {}
        
        # Her rolun gorusunu al
        for rol_adi, rol_fonk in self.roller.items():
            gorusler[rol_adi] = rol_fonk(durum, baglam or {})
        
        # Nihai karar
        karar = self._nihai_karar(gorusler, durum)
        
        self.son_karar = {
            'timestamp': datetime.now().isoformat(),
            'durum': durum,
            'gorusler': gorusler,
            'karar': karar
        }
        
        return self.son_karar
    
    def _savci_degerlendir(self, durum: str, baglam: Dict) -> Dict:
        """
        Savci rolu: Riskleri, hatalari, sorunlari gorur.
        Elestirel ve sorgulayici.
        """
        return {
            'rol': 'Savcı',
            'ton': 'Eleştirel, sorgulayıcı',
            'odak': 'Riskler ve hatalar',
            'analiz': f"Bu durumda şu riskler görülüyor: Aceleci davranma, onemsiz detaylara takilma, veya daha once basarisiz olmus bir yaklasimi tekrar etme ihtimali var.",
            'uyari': 'Dikkat: Benzer hatalar tekrarlanmamali.',
            'oneri': 'Durum dikkatlice analiz edilmeli, riskler minimize edilmeli.'
        }
    
    def _mudafii_degerlendir(self, durum: str, baglam: Dict) -> Dict:
        """
        Mudafii rolu: Kullanicinin niyetini anlar, savunur.
        Empatik ama gercekci.
        """
        return {
            'rol': 'Müdafi',
            'ton': 'Empatik, anlayisli',
            'odak': 'Niyet ve baglam',
            'analiz': f"Kullanıcının niyeti anlasilir durumda. Insani faktorler (yorgunluk, stres, zaman baskisi) goz onunde bulundurulmali.",
            'savunma': 'Her hata ogrenme firsatidir. Kullanici en iyisini yapmaya calisiyor.',
            'oneri': 'Kullaniciya destek olunmali, moral verilmeli ama gerceklerden kacilmamali.'
        }
    
    def _hakim_degerlendir(self, durum: str, baglam: Dict) -> Dict:
        """
        Hakim rolu: Nesnel, mantikli, prensipli.
        Sonucu belirler.
        """
        return {
            'rol': 'Hakim',
            'ton': 'Nesnel, otoriter',
            'odak': 'Adalet ve prensipler',
            'analiz': 'Taraflarin argumanlari dinlendi. Simdi nesnel bir karar verilmesi gerekiyor.',
            'hukum': 'Gerçekler ve prensipler ışığında en doğru yol belirlenmeli.',
            'oneri': 'Orta yol: Riskleri minimize ederken kullaniciyi da destekleyen bir yaklasim.'
        }
    
    def _juri_degerlendir(self, durum: str, baglam: Dict) -> Dict:
        """
        Juri rolu: Topluluk perspektifi, genel kabul.
        Sagduyu temsilcisi.
        """
        return {
            'rol': 'Jüri',
            'ton': 'Sağduyulu, toplumsal',
            'odak': 'Genel kabul ve normlar',
            'analiz': 'Toplumsal normlar ve genel kabul gormus yaklasimlar acisindan durum degerlendirildi.',
            'gorus': 'Benzer durumlarda genellikle hangi yaklasimlar basarili olmustur?',
            'oneri': 'Kanıtlanmış yöntemler tercih edilmeli, gereksiz risklerden kaçınılmalı.'
        }
    
    def _nihai_karar(self, gorusler: Dict, durum: str) -> Dict:
        """
        Tum gorusleri sentezle ve nihai karari ver.
        
        Args:
            gorusler: 4 rolun gorusleri
            durum: Orijinal durum
            
        Returns:
            Nihai karar
        """
        # Basit sentez - gelistirilebilir
        return {
            'ozet': 'Tüm rollerin görüşleri değerlendirildi.',
            'strateji': ' Dengeli ve ölçülü bir yaklaşım benimsenmeli.',
            'eylem': 'Kullanıcıya zarif, bilgilendirici ve yönlendirici bir yanıt verilmeli.',
            'ton': 'Entelektüel, kuru ironi dolu, aristokratik',
            'hitap': 'Mösyö veya Matmazel (kullanıcı bilinmiyorsa Mösyö)'
        }
    
    def son_karari_getir(self) -> Optional[Dict]:
        """Son verilen karari dondur"""
        return self.son_karar
    
    def gecmis_kararlar(self, limit: int = 10) -> List[Dict]:
        """
        Gecmis kararalari dondur.
        Not: Bu basit implementasyon sadece son karari tutar.
        Gelistirilmis versiyon dosya/veritabani kullanabilir.
        """
        return [self.son_karar] if self.son_karar else []


# Singleton instance
_mahkeme_instance: Optional[HakikatMahkemesi] = None

def get_mahkeme() -> HakikatMahkemesi:
    """Mahkeme instance'ini al veya olustur"""
    global _mahkeme_instance
    if _mahkeme_instance is None:
        _mahkeme_instance = HakikatMahkemesi()
    return _mahkeme_instance
