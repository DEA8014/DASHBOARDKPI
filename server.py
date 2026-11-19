import http.server
import socketserver
import os
import json
import urllib.parse
from datetime import datetime

PORT = int(os.environ.get("PORT", 8089))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
META_PATH = os.path.join(DATA_DIR, "metadata.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_meta():
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_meta(meta):
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/status":
            meta = load_meta()
            pyg_file = os.path.join(DATA_DIR, "pyg.xlsx")
            tkt_file = os.path.join(DATA_DIR, "tkt.xlsx")
            resp = {
                "pyg": {
                    "exists": os.path.exists(pyg_file),
                    "filename": meta.get("pyg_name", "RESULTADOS P y G 2026.xlsx"),
                    "updated": meta.get("pyg_updated", "")
                },
                "tkt": {
                    "exists": os.path.exists(tkt_file),
                    "filename": meta.get("tkt_name", "TKT mensuales.xlsx"),
                    "updated": meta.get("tkt_updated", "")
                }
            }
            data = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path in ("/api/files/pyg", "/api/files/tkt"):
            ftype = "pyg" if parsed.path.endswith("pyg") else "tkt"
            fpath = os.path.join(DATA_DIR, f"{ftype}.xlsx")
            if not os.path.exists(fpath):
                self.send_response(404)
                self.end_headers()
                return
            with open(fpath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/api/upload/pyg", "/api/upload/tkt"):
            ftype = "pyg" if parsed.path.endswith("pyg") else "tkt"
            length = int(self.headers.get("Content-Length", 0))
            raw_name = self.headers.get("X-Filename", f"{ftype}.xlsx")
            filename = urllib.parse.unquote(raw_name)
            body = self.rfile.read(length)

            fpath = os.path.join(DATA_DIR, f"{ftype}.xlsx")
            with open(fpath, "wb") as f:
                f.write(body)

            meta = load_meta()
            meta[f"{ftype}_name"] = filename
            meta[f"{ftype}_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_meta(meta)

            resp = json.dumps({"ok": True, "filename": filename}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/clear":
            for fn in ("pyg.xlsx", "tkt.xlsx", "metadata.json"):
                p = os.path.join(DATA_DIR, fn)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            resp = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return
        self.send_response(404)
        self.end_headers()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    print(f"============================================================")
    print(f" Dashboard P&L El Hornero - Contenedor Activo")
    print(f" Escuchando en: http://0.0.0.0:{PORT} (Local: http://localhost:{PORT})")
    print(f" Carpeta de persistencia Excel: {DATA_DIR}")
    print(f"============================================================")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
