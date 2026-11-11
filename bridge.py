#!/usr/bin/env python3
"""Local HTTP bridge between the Vantage MT5 Expert Advisor and the dashboard."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone
import json
import threading

ROOT = Path(__file__).resolve().parent
STATE = {"connected": False}
LOCK = threading.Lock()
STALE_AFTER_SECONDS = 10

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def do_POST(self):
        if self.path != "/api/tick":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16384:
                self.send_error(400, "Invalid payload size")
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            bid, ask = float(data["bid"]), float(data["ask"])
            if bid <= 0 or ask <= 0 or ask < bid:
                raise ValueError("Invalid bid/ask")
            now = datetime.now(timezone.utc).timestamp()
            with LOCK:
                STATE.update(data)
                STATE["received_at"] = now
                STATE["connected"] = True
            self.send_response(204)
            self.end_headers()
        except Exception as exc:
            self.send_error(400, str(exc))

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/quote":
            with LOCK:
                data = dict(STATE)
            fresh = data.get("received_at", 0) and (datetime.now(timezone.utc).timestamp() - data["received_at"] <= STALE_AFTER_SECONDS)
            data["connected"] = bool(fresh)
            if data.get("received_at"):
                data["time"] = datetime.fromtimestamp(data["received_at"], timezone.utc).astimezone().isoformat()
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Dashboard: http://127.0.0.1:8765")
    print("MT5 EA endpoint: http://127.0.0.1:8765/api/tick")
    print("Stop with Ctrl+C")
    server.serve_forever()
