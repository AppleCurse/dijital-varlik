#!/usr/bin/env python3
"""
Dijital Varlik — Kendi Kendini Kuran Bootstrap Sistemi
Eksik repolari klonlar, baglantilari test eder, konfigurasyonu onarir.
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


# ================================================================
# REPO KAYDI — Klonlanacak repolar
# ================================================================

REPOS = {
    "openclaw-main": {
        "url": "https://github.com/NiceLabs/OpenClaw.git",
        "branch": "main",
        "description": "WhatsApp/Telegram mesajlasma istihbarati",
        "required": False,
    },
    "agent-reach-main": {
        "url": "https://github.com/lichar-ai/agent-reach.git",
        "branch": "main",
        "description": "Sosyal medya istihbarati (Reddit, Twitter, TikTok)",
        "required": False,
    },
}

# ================================================================
# SERVIS KONTROL LISTESI
# ================================================================

SERVISLER = [
    ("9router API", "http://localhost:20128/api/health", None),
    ("Browserless CDP", "http://localhost:3001/json/version", None),
    ("LiteLLM Proxy", "http://localhost:4000/health", "omniroute"),
    ("Open WebUI", "http://localhost:3000", None),
    ("Code Server", "http://localhost:8080", None),
]

# ================================================================
# KONFIGURASYON SABLONU
# ================================================================

ENV_TEMPLATE = """LITELLM_URL=http://localhost:20128/v1
LITELLM_KEY={api_key}
MAHKEME_MODEL=gemini/gemini-2.5-flash
FALLBACK_MODEL=gemini/gemini-2.5-flash-lite
BROWSERLESS_URL=http://localhost:3001
MEM0_DATA_DIR=./altyapi/mem0_data
LETTA_DATA_DIR=./altyapi/letta_data
"""


class Bootstrap:
    """Kendi kendini kuran sistem yoneticisi."""

    def __init__(self):
        self.rapor = {
            "tarih": datetime.now().isoformat(),
            "kontroller": {},
            "eylemler": [],
            "durum": "basladi",
        }

    # ----------------------------------------------------------
    # REPO ISLEMLERI
    # ----------------------------------------------------------

    def repo_klonla(self, name: str, info: dict) -> bool:
        """Tek bir repoyu klonla."""
        hedef = ROOT / name
        if hedef.exists():
            print(f"  ✅ {name} zaten var")
            self.rapor["kontroller"][name] = "mevcut"
            return True

        # Github token kontrolu
        token = os.getenv("GITHUB_TOKEN", "")
        if not token and "github.com" in info["url"]:
            if info.get("required"):
                print(f"  ⚠️  {name}: GITHUB_TOKEN yok, klonlanamadi (zorunlu)")
                self.rapor["kontroller"][name] = "TOKEN_YOK"
                return False
            else:
                print(f"  ⏭️  {name} atlandi (GITHUB_TOKEN yok, opsiyonel)")
                self.rapor["kontroller"][name] = "atlandi_token_yok"
                return True

        print(f"  📥 {name} klonlaniyor... ({info['description']})")
        try:
            url = info["url"]
            if token and "github.com" in url:
                url = url.replace("https://", f"https://{token}@")
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", info["branch"],
                 url, str(hedef)],
                check=True, capture_output=True, timeout=120,
                cwd=str(ROOT)
            )
            print(f"  ✅ {name} klonlandi")
            self.rapor["kontroller"][name] = "klonlandi"
            self.rapor["eylemler"].append(f"Repo klonlandi: {name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {name} klonlanamadi: {e.stderr.decode()[:200] if e.stderr else e}")
            self.rapor["kontroller"][name] = f"HATA: {e}"
            return False

    def tum_repolari_kontrol_et(self):
        """Tum eksik repolari kontrol et ve klonla."""
        print("\n" + "=" * 50)
        print("  REPO KONTROLU")
        print("=" * 50)

        for name, info in REPOS.items():
            self.repo_klonla(name, info)

        # Mevcut repolari tara
        git_repolari = []
        for d in ROOT.iterdir():
            if d.is_dir() and (d / ".git").exists():
                git_repolari.append(d.name)
        print(f"\n  Toplam Git reposu: {len(git_repolari)}")
        self.rapor["git_repolari"] = git_repolari

    # ----------------------------------------------------------
    # SERVIS KONTROLLERI
    # ----------------------------------------------------------

    def servis_kontrol(self, name: str, url: str, auth_key: str = None) -> dict:
        """Tek bir servisi kontrol et."""
        try:
            import requests
            headers = {}
            if auth_key:
                headers["Authorization"] = f"Bearer {auth_key}"
            r = requests.get(url, headers=headers, timeout=5)
            ok = r.status_code == 200
            durum = f"OK ({r.status_code})" if ok else f"HATA ({r.status_code})"
            return {"calisiyor": ok, "durum": durum, "kod": r.status_code}
        except Exception as e:
            return {"calisiyor": False, "durum": str(e)[:80], "kod": 0}

    def tum_servisleri_kontrol_et(self):
        """Tum servisleri kontrol et."""
        print("\n" + "=" * 50)
        print("  SERVIS KONTROLU")
        print("=" * 50)

        for name, url, auth in SERVISLER:
            sonuc = self.servis_kontrol(name, url, auth)
            icon = "✅" if sonuc["calisiyor"] else "❌"
            print(f"  {icon} {name}: {sonuc['durum']}")
            self.rapor["kontroller"][f"servis_{name}"] = sonuc

    # ----------------------------------------------------------
    # KONFIGURASYON ONARIMI
    # ----------------------------------------------------------

    def config_onar(self):
        """Config dosyalarini kontrol et ve eksikse olustur."""
        print("\n" + "=" * 50)
        print("  KONFIGURASYON KONTROLU")
        print("=" * 50)

        # .env dosyasi
        env_path = ROOT / "config" / ".env"
        if not env_path.exists():
            api_key = os.getenv("OPENROUTER_API_KEY",
                                "sk-5762d1405cedb9c7-txz14a-1ae81231")
            env_path.parent.mkdir(parents=True, exist_ok=True)
            env_path.write_text(ENV_TEMPLATE.format(api_key=api_key))
            print("  ✅ config/.env olusturuldu")
            self.rapor["eylemler"].append("config/.env olusturuldu")
        else:
            print("  ✅ config/.env mevcut")

        # litellm-config.yaml
        litellm_path = ROOT / "litellm-config.yaml"
        if not litellm_path.exists():
            self._olustur_litellm_config(litellm_path)
            print("  ✅ litellm-config.yaml olusturuldu")
            self.rapor["eylemler"].append("litellm-config.yaml olusturuldu")
        else:
            print("  ✅ litellm-config.yaml mevcut")

    def _olustur_litellm_config(self, path: Path):
        path.write_text("""model_list:
  - model_name: "9router"
    litellm_params:
      model: "openai/gemini/gemini-2.5-flash"
      api_base: "http://172.23.100.38:20128/v1"
      api_key: "sk-5762d1405cedb9c7-txz14a-1ae81231"
  - model_name: "9router-lite"
    litellm_params:
      model: "openai/gemini/gemini-2.5-flash-lite"
      api_base: "http://172.23.100.38:20128/v1"
      api_key: "sk-5762d1405cedb9c7-txz14a-1ae81231"

general_settings:
  master_key: "omniroute"
  port: 4000
""")

    # ----------------------------------------------------------
    # PYTHON PAKET KONTROLU
    # ----------------------------------------------------------

    def paket_kontrol(self):
        """Kritik Python paketlerini kontrol et."""
        print("\n" + "=" * 50)
        print("  PAKET KONTROLU")
        print("=" * 50)

        # (pip_adi, import_adi)
        kritik_paketler = [
            ("litellm", "litellm"),
            ("smolagents", "smolagents"),
            ("browser-use", "browser_use"),
            ("mem0ai", "mem0"),
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("requests", "requests"),
            ("httpx", "httpx"),
            ("pydantic", "pydantic"),
            ("python-dotenv", "dotenv"),
            ("pyyaml", "yaml"),
            ("faster-whisper", "faster_whisper"),
            ("sounddevice", "sounddevice"),
        ]

        eksik = []
        for pip_adi, import_adi in kritik_paketler:
            try:
                __import__(import_adi)
                print(f"  ✅ {pip_adi}")
            except ImportError:
                print(f"  ❌ {pip_adi} EKSIK")
                eksik.append(pip_adi)

        if eksik:
            print(f"\n  📦 {len(eksik)} paket eksik. Kurmak icin:")
            print(f"     pip install {' '.join(eksik)}")
            self.rapor["eylemler"].append(f"Eksik paketler: {eksik}")

        self.rapor["eksik_paketler"] = eksik

    # ----------------------------------------------------------
    # ANA CALISTIRMA
    # ----------------------------------------------------------

    def calistir(self, auto_fix: bool = True):
        """Tam bootstrap dongusu."""
        print("=" * 50)
        print("  DIJITAL VARLIK — BOOTSTRAP")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        # 1. Konfigurasyon
        self.config_onar()

        # 2. Repo klonlama
        self.tum_repolari_kontrol_et()

        # 3. Servis kontrolu
        self.tum_servisleri_kontrol_et()

        # 4. Paket kontrolu
        self.paket_kontrol()

        # 5. Ozet
        print("\n" + "=" * 50)
        print("  BOOTSTRAP TAMAMLANDI")
        print("=" * 50)

        self.rapor["durum"] = "tamamlandi"
        return self.rapor


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dijital Varlik Bootstrap")
    parser.add_argument("--check-only", action="store_true",
                        help="Sadece kontrol et, duzeltme yapma")
    parser.add_argument("--json", action="store_true",
                        help="JSON formatinda rapor")
    args = parser.parse_args()

    b = Bootstrap()
    rapor = b.calistir(auto_fix=not args.check_only)

    if args.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
