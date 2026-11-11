"""Offline checks: python scripts/selftest.py
Covers the database, quiz parsing, the Ollama client (against a fake server) and opens every page headlessly.
"""
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from StudiOS import config
from StudiOS.core import quiz, stats
from StudiOS.core.context import build_system_prompt
from StudiOS.core.db import Database
from StudiOS.core.ollama import OllamaClient, OllamaError


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, body, lines=False):
        self.send_response(200)
        self.end_headers()
        for part in (body if lines else [body]):
            self.wfile.write((json.dumps(part) + "\n").encode())

    def do_GET(self):
        self._send({"models": [{"name": "llama3.2:1b", "size": 1_000_000_000}]})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if req.get("format") == "json":
            q = {"questions": [{"q": "F = ?", "options": ["ma", "mv", "m/a", "a/m"], "answer": "A", "explanation": "Newton"}]}
            self._send({"message": {"content": json.dumps(q)}})
        else:
            self._send([{"message": {"content": "Hel"}}, {"message": {"content": "lo"}, "done": True}], lines=True)


def main():
    tmp = Path(tempfile.mkdtemp())
    # database
    db = Database(tmp / "t.db")
    n = db.add("notes", title="Newton", body="F = ma", subject="Physics")
    db.update("notes", n["id"], body="F = m a")
    assert db.get("notes", n["id"])["body"] == "F = m a"
    assert len(db.list("notes", subject="Physics")) == 1
    db.set_profile(name="Asha")
    assert db.profile()["name"] == "Asha" and db.profile()["modules"]
    backup = db.export_all()
    db.reset()
    assert not db.list("notes")
    db.import_all(backup)
    assert db.list("notes")[0]["title"] == "Newton"
    print("ok  database + backup")

    # quiz parsing
    items = quiz.normalize("mcq", {"questions": [{"q": "x", "options": ["a", "b"], "answer": "B"}, {"q": "bad"}]})
    assert len(items) == 1 and items[0]["answer"] == 1
    assert quiz.normalize("flash", {"cards": [{"front": "a", "back": "b"}, {"front": "only"}]}) == [{"front": "a", "back": "b"}]
    assert "F = ma" in build_system_prompt("JEE", None, "Physics", [{"title": "N", "body": "F = ma"}])
    print("ok  quiz parsing + context")

    # ollama client
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    cfg = {**config.DEFAULT_OLLAMA, "host": f"http://127.0.0.1:{srv.server_port}"}
    cli = OllamaClient(lambda: cfg)
    s = cli.status()
    assert s["running"] and s["active"] == "llama3.2:1b" and not s["preferred_installed"]
    got = []
    assert cli.chat_stream([{"role": "user", "content": "hi"}], got.append)["text"] == "Hello"
    assert quiz.normalize("mcq", cli.chat_json([{"role": "user", "content": "q"}]))[0]["answer"] == 0
    off = OllamaClient(lambda: {**cfg, "host": "http://127.0.0.1:1"}).status()
    assert not off["running"] and "not running" in off["error"]
    srv.shutdown()
    print("ok  ollama client (stream, json, fallback, offline)")

    # GUI smoke test: every page opens
    from PySide6.QtWidgets import QApplication
    from StudiOS.runtime import AppContext
    from StudiOS.ui.main_window import MainWindow
    from StudiOS.ui.theme import QSS
    from StudiOS.ui.pages import PAGES
    app = QApplication([])
    app.setStyleSheet(QSS)
    ctx = AppContext(tmp / "gui")
    ctx.db.set_profile(setup_complete=True, name="Asha", exam="JEE")
    ctx.db.add("courses", title="Physics PW", subject="Physics", platform="Physics Wallah", url="", description="", progress=40)
    win = MainWindow(ctx)
    win.show()
    for pid in PAGES:
        win.go(pid)
        app.processEvents()
    print("ok  all", len(PAGES), "pages open")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
