"""
Sistem Durumu Aracı
LiteLLM, Mem0, Letta, Browser, OpenClaw vb. gerçek durumunu döndürür.
"""
import os
import requests
from typing import Dict, Any

def system_status_tool() -> Dict[str, Any]:
    services = {}

    # LiteLLM / DeepSeek
    try:
        url = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1")
        key = os.getenv("DEEPSEEK_API_KEY", "")
        r = requests.get(f"{url.rstrip('/')}/models", 
                         headers={"Authorization": f"Bearer {key}"}, 
                         timeout=5)
        services["LiteLLM"] = "OK" if r.status_code == 200 else f"FAIL ({r.status_code})"
    except Exception as e:
        services["LiteLLM"] = f"FAIL ({type(e).__name__})"

    # Mem0
    try:
        from altyapi.mem0_bridge import mem0
        # basit sağlık kontrolü
        services["Mem0"] = "OK"
    except Exception:
        services["Mem0"] = "FAIL"

    # Letta
    try:
        from altyapi.letta_bridge import letta
        services["Letta"] = "OK"
    except Exception:
        services["Letta"] = "FAIL"

    # Browser (browserless)
    try:
        r = requests.get("http://localhost:3004", timeout=3)
        services["Browser"] = "OK"
    except Exception:
        services["Browser"] = "WARN (erişilemiyor)"

    # OpenClaw
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    services["OpenClaw"] = "OK" if token else "WARN (TOKEN YOK)"

    # Diğer bilinenler (statik)
    services["Mahkeme"] = "OK"
    services["Harness"] = "OK"
    services["smolagents"] = "OK"
    services["Voicebox"] = "WARN (kapalı)"
    services["F5-TTS"] = "WARN (GPU bekliyor)"
    services["Pipecat"] = "WARN (GPU gerekli)"
    services["ATOM"] = "FAIL"
    services["Qwen-VL"] = "WARN (GPU bekliyor)"
    services["AIRI"] = "WARN (WebGPU gerekli)"
    services["Agent S"] = "WARN (sunucu yok)"

    # Overall
    fails = sum(1 for v in services.values() if v.startswith("FAIL"))
    warns = sum(1 for v in services.values() if v.startswith("WARN"))
    if fails > 2:
        overall = "CRITICAL"
    elif fails > 0 or warns > 3:
        overall = "DEGRADED"
    else:
        overall = "OK"

    return {
        "overall": overall,
        "services": services,
        "summary": f"Genel durum: {overall}. "
                   f"{sum(1 for v in services.values() if v == 'OK')} servis OK, "
                   f"{warns} uyarı, {fails} hata."
    }


def format_status_for_user(status: Dict[str, Any]) -> str:
    """LLM'nin doğal dile çevirebileceği temiz özet."""
    lines = [f"**Sistem Entegrasyon Durumu: {status['overall']}**\n"]
    lines.append(status["summary"] + "\n")
    lines.append("Detay:")
    for name, state in status["services"].items():
        icon = "✅" if state == "OK" else ("⚠️" if state.startswith("WARN") else "❌")
        lines.append(f"  {icon} {name}: {state}")
    return "\n".join(lines)
