#!/usr/bin/env python3
"""
Dijital Varlik — Ana Baslatici
Agentik Dongu'yu baslatir, CLI ve test komutlarini yonetir.
"""
import sys
import os
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def cmd_test():
    """Toplu sistem testini calistir."""
    from agentik_dongu import AgentikDongu
    dongu = AgentikDongu()
    try:
        dongu.toplu_test()
    finally:
        dongu.kapat()


def cmd_durum():
    """Sistem durumunu JSON olarak yazdir."""
    from agentik_dongu import AgentikDongu
    import json
    dongu = AgentikDongu()
    try:
        print(json.dumps(dongu.durum(), ensure_ascii=False, indent=2))
    finally:
        dongu.kapat()


def cmd_calistir(gorev: str):
    """Tek bir gorev calistir."""
    from agentik_dongu import AgentikDongu
    dongu = AgentikDongu()
    try:
        sonuc = dongu.calistir(gorev)
        print(f"\nSONUC: {sonuc.get('status', '?')}")
        if sonuc.get('message'):
            print(f"  {sonuc['message'][:300]}")
    finally:
        dongu.kapat()


def cmd_dongu(adim: int = 5):
    """Interaktif dongu modu."""
    from agentik_dongu import AgentikDongu
    dongu = AgentikDongu()
    try:
        print(f"\nAGENTIK DONGU MODU ({adim} adim)")
        print("Her adimda gorev girebilir, 'q' ile cikabilirsiniz.\n")
        for i in range(adim):
            try:
                gorev = input(f"[{i+1}/{adim}] Gorev (q=cikis): ").strip()
                if gorev.lower() == 'q':
                    break
                if not gorev:
                    continue
                dongu.calistir(gorev)
            except KeyboardInterrupt:
                print("\nDongu durduruldu.")
                break
    finally:
        dongu.kapat()


def cmd_check():
    """Hizli baglanti kontrolu - servisleri test et."""
    import requests

    print("=" * 50)
    print("  BAGLANTI KONTROLU")
    print("=" * 50)

    checks = [
        ("9router API", "http://localhost:20128/api/health"),
        ("Browserless", "http://localhost:3001/json/version"),
        ("LiteLLM", "http://localhost:4000/health"),
        ("Open WebUI", "http://localhost:3000"),
    ]

    for name, url in checks:
        try:
            r = requests.get(url, timeout=5)
            ok = "✅" if r.status_code == 200 else f"⚠️ {r.status_code}"
            print(f"  {ok} {name}: {url}")
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:60]}")

    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Dijital Varlik — Agentik Dongu Baslatici",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  python run.py test           # Toplu sistem testi
  python run.py durum          # Sistem durum raporu
  python run.py calistir "saat kac?"   # Tek gorev
  python run.py dongu          # Interaktif mod (5 adim)
  python run.py dongu --adim 10  # Interaktif mod (10 adim)
  python run.py check          # Baglanti kontrolu
        """
    )
    parser.add_argument("komut", nargs="?", default="test",
                        choices=["test", "durum", "calistir", "dongu", "check"])
    parser.add_argument("gorev", nargs="?", help="Calistirilacak gorev metni")
    parser.add_argument("--adim", type=int, default=5, help="Dongu modu adim sayisi")

    args = parser.parse_args()

    if args.komut == "test":
        cmd_test()
    elif args.komut == "durum":
        cmd_durum()
    elif args.komut == "calistir":
        gorev = args.gorev or input("Gorev: ")
        cmd_calistir(gorev)
    elif args.komut == "dongu":
        cmd_dongu(args.adim)
    elif args.komut == "check":
        cmd_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
