"""Ollama client using only urllib. Runs in the desktop process, so there is no CORS to configure.
API reference: https://github.com/ollama/ollama/blob/main/docs/api.md
"""
import json
import urllib.error
import urllib.request

OFFLINE_MSG = "Ollama is not running. Start the Ollama app, or run 'ollama serve' in a terminal."


class OllamaError(Exception):
    pass


def same_model(a, b):
    norm = lambda m: m if ":" in m else f"{m}:latest"
    return norm(a) == norm(b)


class OllamaClient:
    def __init__(self, get_cfg):
        self.cfg = get_cfg  # callable returning the live settings dict

    def _open(self, path, payload=None, timeout=120):
        url = self.cfg()["host"].rstrip("/") + path
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:300]
            raise OllamaError(f"Ollama returned HTTP {e.code}. {body}")
        except OSError:
            raise OllamaError(OFFLINE_MSG)

    @staticmethod
    def _lines(resp):
        for raw in resp:
            raw = raw.strip()
            if raw:
                yield json.loads(raw)

    def status(self):
        """Never raises. Says whether Ollama is up and which model StudiOS will use."""
        cfg = self.cfg()
        out = {"running": False, "host": cfg["host"], "preferred": cfg["model"], "active": None,
               "preferred_installed": False, "model_ready": False, "installed": [], "error": None}
        try:
            with self._open("/api/tags", timeout=3) as resp:
                models = json.loads(resp.read()).get("models", [])
            out["running"] = True
            out["installed"] = [{"name": m["name"], "size": m.get("size", 0)} for m in models]
            names = [m["name"] for m in out["installed"]]
            out["preferred_installed"] = any(same_model(n, cfg["model"]) for n in names)
            for cand in [cfg["model"], *cfg["fallback_models"]]:
                hit = next((n for n in names if same_model(n, cand)), None)
                if hit:
                    out["active"] = hit
                    break
            out["active"] = out["active"] or (names[0] if names else None)
            out["model_ready"] = out["active"] is not None
        except (OllamaError, ValueError) as e:
            out["error"] = str(e)
        return out

    def _model(self, requested=None):
        if requested:
            return requested
        s = self.status()
        if not s["running"]:
            raise OllamaError(s["error"])
        if not s["model_ready"]:
            raise OllamaError(f"No model installed. Run: ollama pull {s['preferred']}")
        return s["active"]

    def _options(self, temperature=None):
        c = self.cfg()
        return {"temperature": c["temperature"] if temperature is None else temperature, "num_ctx": c["num_ctx"]}

    def pull(self, model, on_progress=lambda p: None, stop=lambda: False):
        with self._open("/api/pull", {"model": model, "stream": True}, timeout=600) as resp:
            for msg in self._lines(resp):
                if msg.get("error"):
                    raise OllamaError(msg["error"])
                total, done = msg.get("total"), msg.get("completed")
                on_progress({"status": msg.get("status", ""), "total": total, "completed": done,
                             "percent": int(done / total * 100) if total and done is not None else None})
                if stop():
                    return

    def chat_stream(self, messages, on_token=lambda t: None, stop=lambda: False, model=None):
        use = self._model(model)
        payload = {"model": use, "messages": messages, "stream": True,
                   "keep_alive": self.cfg()["keep_alive"], "options": self._options()}
        text = ""
        with self._open("/api/chat", payload) as resp:
            for msg in self._lines(resp):
                if msg.get("error"):
                    raise OllamaError(msg["error"])
                piece = msg.get("message", {}).get("content", "")
                if piece:
                    text += piece
                    on_token(piece)
                if stop():
                    break
        return {"model": use, "text": text}

    def chat_json(self, messages, model=None):
        """Non-streaming call that forces valid JSON. Used for quiz and plan generation."""
        use = self._model(model)
        payload = {"model": use, "messages": messages, "stream": False, "format": "json",
                   "keep_alive": self.cfg()["keep_alive"], "options": self._options(0.2)}
        with self._open("/api/chat", payload, timeout=300) as resp:
            body = json.loads(resp.read())
        try:
            return json.loads(body["message"]["content"])
        except (KeyError, ValueError):
            raise OllamaError("The model did not return valid JSON. Try again.")
