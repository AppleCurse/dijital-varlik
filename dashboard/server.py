#!/usr/bin/env python3
"""Dijital Varlik Dashboard — Tek Arayüz."""
import http.server, json, subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
VENV = str(ROOT / ".venv" / "bin" / "python3")
sys.path.insert(0, str(ROOT))

class D(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT/"dashboard"), **kw)

    def do_GET(self):
        if self.path == "/api/status":
            self._json(self._status())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            msg = body.get("message","")
            try:
                r = subprocess.run([VENV, str(ROOT/"otonom.py"), "--once", msg],
                    capture_output=True, text=True, timeout=90, cwd=str(ROOT),
                    env={**os.environ, "BROWSERLESS_URL": "http://localhost:3004"})
                ans = ""
                for line in r.stdout.splitlines():
                    if line.startswith("✅ "): ans = line[2:]; break
                if not ans: ans = r.stdout.strip()[-500:]
            except Exception as e: ans = f"Hata: {e}"
            self._json({"answer": ans})

        elif self.path == "/api/status":
            self._json(self._status())

    def _status(self):
        s = {}
        try:
            import requests; r=requests.get("http://172.23.96.1:20128/api/health",timeout=3)
            s["9router"]="ON" if r.status_code==200 else "OFF"
        except: s["9router"]="OFF"
        try:
            import requests; r=requests.get("http://localhost:3004/json/version",timeout=3)
            s["browser"]="ON" if r.status_code==200 else "OFF"
        except: s["browser"]="OFF"
        try:
            import torch; s["gpu"]=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "YOK"
        except: s["gpu"]="YOK"
        try:
            import psutil; s["ram"]=f"{psutil.virtual_memory().percent}%"
        except: s["ram"]="?"
        return s

    def _json(self, d):
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def log_message(self, *a): pass

if __name__=="__main__":
    p=int(sys.argv[1]) if len(sys.argv)>1 else 9998
    print(f"Dashboard: http://0.0.0.0:{p}")
    http.server.HTTPServer(("0.0.0.0",p), D).serve_forever()
