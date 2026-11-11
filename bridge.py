#!/usr/bin/env python3
"""Local Vantage MT5 quote bridge plus public Telegram XAUUSD signal reader."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json, re, threading, time

ROOT = Path(__file__).resolve().parent
STATE = {"connected": False}
LOCK = threading.Lock()
STALE_AFTER_SECONDS = 10
TELEGRAM_SOURCES = [
    {"name": "SureShot GOLD", "username": "ssfgold", "url": "https://t.me/s/ssfgold"},
    {"name": "XAU Empire", "username": "xauempirefx", "url": "https://t.me/s/xauempirefx"},
    {"name": "SignalProvider", "username": "Free_signals", "url": "https://t.me/s/Free_signals"},
]
TG_STATE = {"checked_at": None, "signals": [], "sources": {}, "errors": {}}
TG_LOCK = threading.Lock()
TG_POLL_SECONDS = 60
MAX_SIGNALS = 100

def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()

class TelegramHTMLParser(HTMLParser):
    """Extract public preview messages from Telegram's t.me/s pages."""
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current = None
        self.capture_text = False
        self.capture_time = False
        self.text_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "tgme_widget_message" in a.get("class", ""):
            self.current = {"id": a.get("data-post", ""), "text": "", "time": ""}
        elif self.current is not None and tag == "div" and "tgme_widget_message_text" in a.get("class", ""):
            self.capture_text = True
            self.text_depth = 1
        elif self.current is not None and self.capture_text and tag in ("br",):
            self.current["text"] += " "
        elif self.current is not None and tag == "time" and a.get("datetime"):
            self.current["time"] = a["datetime"]

    def handle_endtag(self, tag):
        if self.capture_text and tag == "div":
            self.text_depth -= 1
            if self.text_depth <= 0:
                self.capture_text = False
        if tag == "div" and self.current is not None and not self.capture_text:
            # Message containers close after their text and metadata.
            pass

    def handle_data(self, data):
        if self.current is not None and self.capture_text:
            self.current["text"] += data

    def close(self):
        super().close()
        # Re-scan using a robust post-id boundary: the parser stores text as it is encountered.
        # A message ends when the next widget message begins; this is handled in feed override.

    def feed(self, data):
        # HTMLParser callbacks are used to extract text; finish current message at next message.
        super().feed(data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

def extract_posts(html):
    # Telegram's public preview uses repeated tgme_widget_message blocks.
        blocks = re.findall(r'<div class="tgme_widget_message[^"]*"[^>]*data-post="([^"]+)"([\s\S]*?)(?=<div class="tgme_widget_message[^"]*"|</section>)', html)
    posts = []
    for post_id, raw in blocks:
        tm = re.search(r'<time[^>]*datetime="([^"]+)"', raw)
        chunks = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>([\s\S]*?)</div>', raw)
        if not chunks:
            continue
        txt = re.sub(r'<br\s*/?>', ' ', chunks[0], flags=re.I)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = clean_text(txt.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'").replace('&quot;', '"'))
        posts.append({"id": post_id, "text": txt, "time": tm.group(1) if tm else None})
    return posts

def parse_signal(post, source):
    text = post.get("text", "")
    upper = text.upper()
    if not re.search(r"\b(XAUUSD|XAU/USD|GOLD)\b", upper):
        return None
    direction_match = re.search(r"\b(BUY|SELL)\b", upper)
    if not direction_match:
        return None
    side = direction_match.group(1)
    sl_match = re.search(r"\b(?:SL|STOP\s*LOSS)\s*[:=@-]?\s*(\d{3,5}(?:\.\d+)?)", upper)
    tp_match = re.search(r"\b(?:TP\s*1?|TAKE\s*PROFIT)\s*[:=@-]?\s*(\d{3,5}(?:\.\d+)?)", upper)
    if not sl_match or not tp_match:
        return None
    entry_match = re.search(r"\bENTRY(?:\s*ZONE)?\s*[:=@-]?\s*(\d{3,5}(?:\.\d+)?)(?:\s*[-–/]\s*(\d{3,5}(?:\.\d+)?))?", upper)
    if not entry_match:
        after_direction = upper[direction_match.end():]
        entry_match = re.search(r"(?:LIMIT|STOP)?\s*[:=@-]?\s*(\d{3,5}(?:\.\d+)?)", after_direction)
    if not entry_match:
        return None
    if entry_match.lastindex and entry_match.lastindex >= 2 and entry_match.group(2):
        entry_low, entry_high = float(entry_match.group(1)), float(entry_match.group(2))
        entry = (entry_low + entry_high) / 2
        entry_label = f"{entry_low:g}–{entry_high:g}"
    else:
        entry = float(entry_match.group(1))
        entry_label = f"{entry:g}"
    sl, tp = float(sl_match.group(1)), float(tp_match.group(1))
    if min(entry, sl, tp) <= 0:
        return None
    # Reject structurally implausible direction/levels instead of guessing.
    if (side == "BUY" and not (sl < entry < tp)) or (side == "SELL" and not (tp < entry < sl)):
        return None
    return {
        "id": post.get("id") or f"{source['username']}:{post.get('time')}:{entry}",
        "source": source["name"], "username": source["username"], "url": source["url"],
        "time": post.get("time"), "side": side, "entry": entry, "entry_label": entry_label,
        "sl": sl, "tp": tp, "status": "NEU", "raw": text[:500]
    }

def refresh_telegram():
    found, source_status, errors = [], {}, {}
    for source in TELEGRAM_SOURCES:
        try:
            req = Request(source["url"], headers={"User-Agent": "Mozilla/5.0 XAUUSD-Dashboard/1.0"})
            with urlopen(req, timeout=12) as response:
                html = response.read(2_500_000).decode("utf-8", "replace")
            posts = extract_posts(html)
            parsed = [s for p in posts if (s := parse_signal(p, source))]
            found.extend(parsed)
            source_status[source["username"]] = {
                "name": source["name"], "ok": True, "posts_seen": len(posts),
                "signals_found": len(parsed), "url": source["url"]
            }
        except Exception as exc:
            source_status[source["username"]] = {"name": source["name"], "ok": False, "url": source["url"]}
            errors[source["username"]] = str(exc)[:220]
    # Preserve history and deduplicate by Telegram post id.
    with TG_LOCK:
        old = {s["id"]: s for s in TG_STATE["signals"]}
        for s in found:
            old.setdefault(s["id"], s)
        ordered = sorted(old.values(), key=lambda x: x.get("time") or "", reverse=True)[:MAX_SIGNALS]
        TG_STATE.update({"checked_at": datetime.now(timezone.utc).isoformat(),
                         "signals": ordered, "sources": source_status, "errors": errors})

def telegram_worker():
    while True:
        refresh_telegram()
        time.sleep(TG_POLL_SECONDS)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/api/tick":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 16384:
                    self.send_error(400, "Invalid payload size")
                    return
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                bid, ask = float(data["bid"]), float(data["ask"])
                if bid <= 0 or ask <= 0 or ask < bid:
                    raise ValueError("Invalid bid/ask")
                with LOCK:
                    STATE.update(data)
                    STATE["received_at"] = datetime.now(timezone.utc).timestamp()
                    STATE["connected"] = True
                self.send_response(204); self.end_headers()
            except Exception as exc:
                self.send_error(400, str(exc))
            return
        if self.path == "/api/telegram-refresh":
            threading.Thread(target=refresh_telegram, daemon=True).start()
            self.send_json({"started": True}, 202)
            return
        self.send_error(404)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/quote":
            with LOCK:
                data = dict(STATE)
            fresh = data.get("received_at") and (datetime.now(timezone.utc).timestamp() - data["received_at"] <= STALE_AFTER_SECONDS)
            data["connected"] = bool(fresh)
            if data.get("received_at"):
                data["time"] = datetime.fromtimestamp(data["received_at"], timezone.utc).astimezone().isoformat()
            self.send_json(data); return
        if path == "/api/telegram-signals":
            with TG_LOCK:
                data = dict(TG_STATE)
            self.send_json(data); return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

if __name__ == "__main__":
    threading.Thread(target=telegram_worker, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Dashboard: http://127.0.0.1:8765")
    print("MT5 EA endpoint: http://127.0.0.1:8765/api/tick")
    print("Public Telegram previews: SureShot GOLD, XAU Empire, SignalProvider")
    print("Telegram preview polling: every 60 seconds; Ctrl+C to stop")
    server.serve_forever()
