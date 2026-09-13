"""Durable runs, events and an explicitly indexed document register."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Repository:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                    filename TEXT NOT NULL, sha256 TEXT NOT NULL,
                    task TEXT NOT NULL, provider TEXT NOT NULL,
                    status TEXT NOT NULL, result TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES runs(id),
                    created_at TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_run ON events(run_id, id);
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, project TEXT NOT NULL,
                    document_number TEXT NOT NULL, revision TEXT NOT NULL,
                    filename TEXT NOT NULL, sha256 TEXT NOT NULL, text TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    UNIQUE(project, document_number, revision, sha256)
                );
                CREATE INDEX IF NOT EXISTS document_lookup
                ON documents(project, document_number);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_run(self, document, task, provider):
        run_id = str(uuid4())
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                       (run_id, utc_now(), document.filename, document.sha256,
                        task, provider, "running"))
        return run_id

    def event(self, run_id, kind, payload):
        with self.connect() as db:
            db.execute("INSERT INTO events(run_id, created_at, kind, payload) VALUES(?,?,?,?)",
                       (run_id, utc_now(), kind, json.dumps(payload, ensure_ascii=False)))

    def finish(self, run_id, status, result):
        with self.connect() as db:
            db.execute("UPDATE runs SET status=?, result=? WHERE id=?",
                       (status, json.dumps(result, ensure_ascii=False), run_id))

    def get_run(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            events = db.execute("SELECT created_at,kind,payload FROM events WHERE run_id=? ORDER BY id",
                                (run_id,)).fetchall()
        if row is None:
            return None
        result = dict(row)
        result["result"] = json.loads(result["result"]) if result["result"] else None
        result["events"] = [{"sequence": i, "timestamp": e["created_at"],
                             "kind": e["kind"], **json.loads(e["payload"])}
                            for i, e in enumerate(events, 1)]
        return result

    def list_runs(self, limit=25, offset=0):
        with self.connect() as db:
            rows = db.execute("SELECT id,created_at,filename,task,provider,status FROM runs "
                              "ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
                              (limit, offset)).fetchall()
        return [dict(row) for row in rows]

    def index(self, document, metadata):
        key = [metadata[f].strip().upper() for f in ("project", "document_number", "revision")]
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO documents VALUES(?,?,?,?,?,?,?,?)",
                       (str(uuid4()), *key, document.filename, document.sha256, document.text, utc_now()))
            row = db.execute("SELECT id,project,document_number,revision,filename,sha256,indexed_at "
                             "FROM documents WHERE project=? AND document_number=? AND revision=? AND sha256=?",
                             (*key, document.sha256)).fetchone()
        return dict(row)

    def revisions(self, project, document_number):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM documents WHERE project=? AND document_number=?",
                              (project.strip().upper(), document_number.strip().upper())).fetchall()
        return [dict(row) for row in rows]
