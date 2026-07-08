"""
Katman 3 — smolagents Köprüsü (Code-Agent Motoru)
Araç kullanmak için anında Python kodu yazıp çalıştıran ajan.
LiteLLM proxy üzerinden LLM'ye bağlanır.
"""
import sys
import os
from typing import Optional

from config.config import config
from altyapi.litellm_bridge import litellm


class SmolAgentBridge:
    """
    smolagents CodeAgent yöneticisi.
    LiteLLM proxy üzerinden LLM'ye bağlanır.
    Dışarıdan araç (tool) enjekte edilebilir.
    """

    def __init__(self, tools: list = None):
        self.model = None
        self._agent_ready = False
        self._custom_tools = tools or []
        self._init_agent()

    def _init_agent(self):
        """smolagents agent'ı LiteLLM proxy ile başlat."""
        try:
            from smolagents import CodeAgent, LiteLLMModel

            # LiteLLM requires provider prefix (openai/) for custom endpoints
            # Model ID: kr/claude-sonnet-4.5 → openai/kr/claude-sonnet-4.5
            model_id = config.MAHKEME_MODEL
            if not model_id.startswith("openai/"):
                model_id = f"openai/{model_id}"

            self.model = LiteLLMModel(
                model_id=model_id,
                api_base=config.LITELLM_URL,
                api_key=config.LITELLM_KEY,
            )
            self.agent = CodeAgent(
                tools=self._custom_tools,
                model=self.model,
                add_base_tools=True,
            )
            self._agent_ready = True
            print(f"[smolagents] CodeAgent ready with {len(self._custom_tools)} tools")
        except Exception as e:
            print(f"[smolagents] Init error: {e}")
            import traceback
            traceback.print_exc()
            self._agent_ready = False

    def calistir(self, gorev: str) -> Optional[str]:
        """
        Bir görevi CodeAgent ile çalıştır.
        Agent ihtiyaca göre Python kodu yazıp araçları kullanır.

        Returns:
            Çalıştırma sonucu metni, veya None (hata)
        """
        if not self._agent_ready:
            return None

        try:
            print(f"[smolagents] Running: {gorev[:100]}...")
            result = self.agent.run(gorev)
            return str(result)
        except Exception as e:
            print(f"[smolagents] Execution error: {e}")
            return None

    def hazir_mi(self) -> bool:
        return self._agent_ready


# Global instance (tools ile yeniden oluşturulabilir)
_smol_instance: Optional[SmolAgentBridge] = None

def get_smol(tools: list = None) -> SmolAgentBridge:
    global _smol_instance
    if _smol_instance is None or tools:
        _smol_instance = SmolAgentBridge(tools=tools)
    return _smol_instance
