#!/usr/bin/env python3
"""Servește folderul preview/ pe 0.0.0.0:8000 ca să vadă bossul rezultatele.

Stă ÎN REPO (nu în /home/user/preview) pentru că sandboxul se resetează și
tot ce e în afara repo-ului dispare. Paginile și elementele servite sunt tot
din repo, deci supraviețuiesc.

Pornire:  python3 preview/serveste.py
"""
import http.server
import json
import os
import socketserver
import sys

PORT = int(os.environ.get("PORT", "8000"))
AICI = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_POST(self):
        """Editorul trimite pozițiile elementelor; le scriem în preview/pozitii.json."""
        n = int(self.headers.get("Content-Length", 0))
        brut = self.rfile.read(n)
        dest = os.path.join(AICI, "pozitii.json")
        try:
            data = json.loads(brut)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print(f"POZITII SALVATE: {dest} ({len(brut)} bytes, "
                  f"{len(data.get('elemente', []))} elemente)", flush=True)
            cod, rasp = 200, b"ok"
        except Exception as e:                                   # pragma: no cover
            print(f"EROARE la salvare: {e}", flush=True)
            cod, rasp = 400, str(e).encode()
        self.send_response(cod)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(rasp)))
        self.end_headers()
        self.wfile.write(rasp)

    def log_message(self, fmt, *args):
        if "/pozitii" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)


def main():
    os.chdir(AICI)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as srv:
        print(f"servesc {AICI} pe 0.0.0.0:{PORT}", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\noprit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
