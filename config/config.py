import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 9Router / OpenRouter Konfigurasyonu
    LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:20128/v1")
    LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-5762d1405cedb9c7-vtowrm-d6ad8046")

    MAHKEME_MODEL = os.getenv("MAHKEME_MODEL", "dijitalvarlik")
    FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "mycombo")

    # Servisler
    BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "http://localhost:3004")

    # Hafiza
    MEM0_DATA_DIR = os.getenv("MEM0_DATA_DIR", "./altyapi/mem0_data")
    LETTA_DATA_DIR = os.getenv("LETTA_DATA_DIR", "./altyapi/letta_data")

    # 9router uyumlulugu
    ROUTER9_URL = LITELLM_URL
    ROUTER9_KEY = LITELLM_KEY

config = Config()
