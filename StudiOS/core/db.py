"""Local SQLite storage using only the standard library.

Every record is a JSON document in one table, grouped by collection name. That keeps adding a
new field to a module a one-line change: no migrations.
"""
import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path

from .. import config

COLLECTIONS = ("courses", "notes", "tasks", "blocks", "sessions", "quizzes", "results")


def _now():
    return datetime.now().isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._c = sqlite3.connect(str(path), check_same_thread=False)
        with self._lock:
            self._c.executescript(
                """
                CREATE TABLE IF NOT EXISTS docs(
                    id TEXT PRIMARY KEY, col TEXT NOT NULL, data TEXT NOT NULL,
                    created TEXT NOT NULL, updated TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS docs_col ON docs(col);
                CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                """
            )
            self._c.commit()

    # ---- documents ----
    @staticmethod
    def _doc(row):
        d = json.loads(row[2])
        d.update(id=row[0], created=row[3], updated=row[4])
        return d

    def _check(self, col):
        if col not in COLLECTIONS:
            raise ValueError(f"Unknown collection: {col}")

    def list(self, col, **where):
        self._check(col)
        with self._lock:
            rows = self._c.execute(
                "SELECT id, col, data, created, updated FROM docs WHERE col=? ORDER BY created", (col,)
            ).fetchall()
        docs = [self._doc(r) for r in rows]
        return [d for d in docs if all(d.get(k) == v for k, v in where.items())]

    def get(self, col, doc_id):
        self._check(col)
        with self._lock:
            r = self._c.execute(
                "SELECT id, col, data, created, updated FROM docs WHERE id=? AND col=?", (doc_id, col)
            ).fetchone()
        return self._doc(r) if r else None

    def add(self, col, **fields):
        self._check(col)
        doc_id, now = uuid.uuid4().hex, _now()
        with self._lock:
            self._c.execute(
                "INSERT INTO docs VALUES (?,?,?,?,?)", (doc_id, col, json.dumps(fields), now, now)
            )
            self._c.commit()
        return self.get(col, doc_id)

    def update(self, col, doc_id, **patch):
        doc = self.get(col, doc_id)
        if not doc:
            raise KeyError(f"{col}/{doc_id} not found")
        for k in ("id", "created", "updated"):
            doc.pop(k)
        doc.update(patch)
        with self._lock:
            self._c.execute(
                "UPDATE docs SET data=?, updated=? WHERE id=?", (json.dumps(doc), _now(), doc_id)
            )
            self._c.commit()
        return self.get(col, doc_id)

    def remove(self, col, doc_id):
        self._check(col)
        with self._lock:
            self._c.execute("DELETE FROM docs WHERE id=? AND col=?", (doc_id, col))
            self._c.commit()

    # ---- key/value settings ----
    def kv_get(self, key, default=None):
        with self._lock:
            r = self._c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else default

    def kv_set(self, key, value):
        with self._lock:
            self._c.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (key, json.dumps(value)))
            self._c.commit()

    def profile(self):
        return {**config.DEFAULT_PROFILE, **self.kv_get("profile", {})}

    def set_profile(self, **patch):
        self.kv_set("profile", {**self.profile(), **patch})

    def ollama_cfg(self):
        return {**config.DEFAULT_OLLAMA, **self.kv_get("ollama", {})}

    def set_ollama(self, **patch):
        self.kv_set("ollama", {**self.kv_get("ollama", {}), **patch})

    # ---- backup ----
    def export_all(self):
        with self._lock:
            kv = {k: json.loads(v) for k, v in self._c.execute("SELECT key, value FROM kv")}
        return {"app": config.APP_NAME, "version": config.VERSION, "kv": kv,
                "docs": {c: self.list(c) for c in COLLECTIONS}}

    def import_all(self, data):
        if "docs" not in data:
            raise ValueError("This file is not a StudiOS backup.")
        self.reset()
        with self._lock:
            for k, v in data.get("kv", {}).items():
                self._c.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (k, json.dumps(v)))
            for col, docs in data["docs"].items():
                if col not in COLLECTIONS:
                    continue
                for d in docs:
                    d = dict(d)
                    i, c, u = d.pop("id"), d.pop("created", _now()), d.pop("updated", _now())
                    self._c.execute("INSERT INTO docs VALUES (?,?,?,?,?)", (i, col, json.dumps(d), c, u))
            self._c.commit()

    def reset(self):
        with self._lock:
            self._c.execute("DELETE FROM docs")
            self._c.execute("DELETE FROM kv")
            self._c.commit()
