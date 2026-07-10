#!/usr/bin/env python3
"""Dijital Varlik Dashboard — Tek Arayüz, Tüm Yetenekler."""
import http.server, json, subprocess, sys, os, base64, tempfile, cgi
from pathlib import Path
from io import BytesIO
ROOT = Path(__file__).resolve().parent.parent
VENV = str(ROOT / ".venv" / "bin" / "python3")
sys.path.insert(0, str(ROOT))

class D(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT/"dashboard"), **kw)

    def do_GET(self):
        if self.path == "/api/status":
            self._json(self._status())
        elif self.path.startswith("/uploads/"):
            path = ROOT / self.path.lstrip("/")
            if path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                self.wfile.write(path.read_bytes())
            else: self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            msg = body.get("message","")
            ans = self._chat(msg)
            self._json({"answer": ans})

        elif self.path == "/api/face":
            # Multipart form: image file
            ctype = self.headers.get("Content-Type","")
            if "multipart" in ctype:
                ans = self._face_analyze()
            else:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                img_b64 = body.get("image","")
                ans = self._face_analyze_b64(img_b64)
            self._json(ans)

        elif self.path == "/api/status":
            self._json(self._status())

        else:
            self.send_error(404)

    def _chat(self, msg):
        # Hızlı yol: Kesici + basit LLM
        try:
            from altyapi.kesici import kesici
            local = kesici.tani(msg)
            if local: return local
        except: pass

        try:
            from altyapi.litellm_bridge import litellm
            r = litellm.chat([{"role":"user","content":msg}], max_tokens=200)
            if r and r.get("content"): return r["content"][:500]
        except: pass

        # Fallback: subprocess otonom
        try:
            r = subprocess.run([VENV, str(ROOT/"otonom.py"), "--once", msg],
                capture_output=True, text=True, timeout=60, cwd=str(ROOT),
                env={**os.environ, "BROWSERLESS_URL": "http://localhost:3004"})
            ans = ""
            for line in r.stdout.splitlines():
                if line.startswith("✅ "): ans = line[2:]; break
            if not ans: ans = r.stdout.strip()[-500:]
            return ans
        except: return "İşlem zaman aşımına uğradı."

    def _face_analyze(self):
        # Multipart form data parsing
        try:
            import cgi
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                environ={"REQUEST_METHOD":"POST","CONTENT_TYPE":self.headers["Content-Type"]})
            if "file" in form:
                f = form["file"]
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                path = ROOT / "dashboard" / "uploads" / f"face_{os.urandom(4).hex()}{ext}"
                (ROOT/"dashboard"/"uploads").mkdir(parents=True, exist_ok=True)
                with open(path, "wb") as out: out.write(f.file.read())
                return self._run_face(str(path))
        except Exception as e: return {"status":"error","message":str(e)}
        return {"status":"error","message":"Dosya yok"}

    def _face_analyze_b64(self, b64):
        if not b64: return {"status":"error","message":"Resim yok"}
        try:
            data = base64.b64decode(b64.split(",")[-1])
            path = ROOT / "dashboard" / "uploads" / f"face_{os.urandom(4).hex()}.jpg"
            (ROOT/"dashboard"/"uploads").mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return self._run_face(str(path))
        except Exception as e: return {"status":"error","message":str(e)[:200]}

    def _run_face(self, img_path):
        try:
            r = subprocess.run([VENV, "-c", f"""
from mudahale.deepface_bridge import get_deepface
df = get_deepface()
result = df.analyze("{img_path}")
import json; print(json.dumps(result, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=60, cwd=str(ROOT))
            return json.loads(r.stdout.strip())
        except Exception as e: return {"status":"error","message":str(e)[:200]}

    def _status(self):
        s = {}
        try:
            import requests; r=requests.get("http://172.23.96.1:20128/api/health",timeout=2)
            s["9router"]="ON" if r.status_code==200 else "OFF"
        except: s["9router"]="OFF"
        try:
            import requests; r=requests.get("http://localhost:3004/json/version",timeout=2)
            s["browser"]="ON" if r.status_code==200 else "OFF"
        except: s["browser"]="OFF"
        try:
            import torch; s["gpu"]=torch.cuda.get_device_name(0).replace("NVIDIA ","") if torch.cuda.is_available() else "YOK"
        except: s["gpu"]="YOK"
        try:
            import sounddevice as sd
            devs=[d for d in sd.query_devices() if d["max_input_channels"]>0]
            s["mic"]=f"{len(devs)} cihaz" if devs else "YOK"
        except: s["mic"]="?"
        try:
            import psutil; s["ram"]=f"{psutil.virtual_memory().percent:.0f}%"; s["cpu"]=f"{psutil.cpu_percent(0.1):.0f}%"
        except: s["ram"]="?"; s["cpu"]="?"
        return s

    def _json(self, d):
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def log_message(self, *a): pass

if __name__=="__main__":
    p=int(sys.argv[1]) if len(sys.argv)>1 else 9998
    print(f"Dashboard: http://0.0.0.0:{p}")
    http.server.HTTPServer(("0.0.0.0",p), D).serve_forever()
