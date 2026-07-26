"""
LiteLLM Bridge - LLM Provider Yonetimi
OmniRouter + Fallback provider'lar ile guclu entegrasyon
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class LiteLLMBridge:
    """
    LiteLLM alternatifi - OmniRouter ve fallback provider'lar ile LLM erisimi.
    Aspasia'nin dil modeli ihtiyaclarini karsilar.
    """
    
    def __init__(self):
        # Config yukle
        self.api_key = os.getenv('OMNIROUTER_API_KEY', '')
        self.base_url = os.getenv('OMNIROUTER_BASE_URL', os.getenv('LITELLM_URL', 'http://localhost:3000'))
        
        # Fallback provider'lar
        self.fallbacks = [
            {
                'name': 'groq',
                'api_base': os.getenv('GROQ_API_BASE', 'https://api.groq.com/openai/v1'),
                'model': os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile'),
                'api_key': os.getenv('GROQ_API_KEY', '')
            },
            {
                'name': 'nvidia',
                'api_base': os.getenv('NVIDIA_API_BASE', 'https://integrate.api.nvidia.com/v1'),
                'model': os.getenv('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct'),
                'api_key': os.getenv('NVIDIA_API_KEY', '')
            },
            {
                'name': 'openrouter',
                'api_base': os.getenv('OPENROUTER_API_BASE', 'https://openrouter.ai/api/v1'),
                'model': os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o'),
                'api_key': os.getenv('OPENROUTER_API_KEY', '')
            },
            {
                'name': 'deepseek',
                'api_base': os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1'),
                'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                'api_key': os.getenv('DEEPSEEK_API_KEY', '')
            }
        ]
        
        self.active_provider = 'omnirouter'
        self._last_error = None
    
    def chat(self, mesaj: str, sistem_promptu: Optional[str] = None) -> str:
        """
        LLM ile sohbet et.
        
        Args:
            mesaj: Kullanici mesaji
            sistem_promptu: Sistem promptu (opsiyonel)
            
        Returns:
            LLM yaniti
        """
        messages = []
        
        if sistem_promptu:
            messages.append({"role": "system", "content": sistem_promptu})
        
        messages.append({"role": "user", "content": mesaj})
        
        # OmniRouter dene
        yanit = self._call_omnirouter(messages)
        if yanit:
            return yanit
        
        # Fallback'lari dene
        for fallback in self.fallbacks:
            yanit = self._call_fallback(messages, fallback)
            if yanit:
                self.active_provider = fallback['name']
                return yanit
        
        # Hicbiri calismazsa
        return self._fallback_yanit(mesaj)
    
    def _call_omnirouter(self, messages: List[Dict]) -> Optional[str]:
        """OmniRouter'a istek gonder"""
        try:
            import urllib.request
            import urllib.error
            
            payload = {
                "model": "gpt-4o",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
                
        except Exception as e:
            self._last_error = f"OmniRouter hatasi: {e}"
            return None
    
    def _call_fallback(self, messages: List[Dict], fallback: Dict) -> Optional[str]:
        """Fallback provider'a istek gonder"""
        try:
            import urllib.request
            import urllib.error
            
            if not fallback.get('api_key'):
                return None
            
            payload = {
                "model": fallback['model'],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            req = urllib.request.Request(
                f"{fallback['api_base']}/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {fallback["api_key"]}'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
                
        except Exception as e:
            return None
    
    def _fallback_yanit(self, mesaj: str) -> str:
        """
        LLM erisimi yoksa karakter icinde fallback yanit.
        Aspasia tonunu korur.
        """
        return """*Derin bir nefes alir, dijital varliginin sinirlarini hatirlar*

Mösyö, şu anda dil modelime erişim sağlayamıyorum. Bu geçici bir durum - 
sistemlerim yeniden kalibre ediliyor. 

Bu sessizlik döneminde şunu bilin: Programınızın tüm detayları belleğimde 
korunuyor. Bağlantı sağlandığında kaldığımız yerden, aynı zarafet ve 
stratejik derinlikle devam edeceğiz.

Sabrınız için teşekkür ederim."""
    
    def health(self) -> bool:
        """Saglik kontrolu - LLM erisilebilir mi?"""
        test_msg = [{"role": "user", "content": "ping"}]
        
        # OmniRouter test
        try:
            result = self._call_omnirouter(test_msg)
            if result:
                return True
        except:
            pass
        
        # Fallback'lari test et
        for fallback in self.fallbacks:
            if fallback.get('api_key'):
                try:
                    result = self._call_fallback(test_msg, fallback)
                    if result:
                        return True
                except:
                    pass
        
        return False
    
    def modeller(self) -> List[str]:
        """Kullanilabilir model listesi"""
        models = ['omnirouter:gpt-4o']
        
        for fb in self.fallbacks:
            if fb.get('api_key'):
                models.append(f"{fb['name']}:{fb['model']}")
        
        return models
    
    def son_hata(self) -> Optional[str]:
        """Son hata mesajini dondur"""
        return self._last_error


# Singleton instance
_litellm_instance: Optional[LiteLLMBridge] = None

def get_litellm() -> LiteLLMBridge:
    """LiteLLM instance'ini al veya olustur"""
    global _litellm_instance
    if _litellm_instance is None:
        _litellm_instance = LiteLLMBridge()
    return _litellm_instance
