import json, sqlite3
from pathlib import Path
from .config import DB_PATH

def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.executescript("""
      CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, actor TEXT NOT NULL, event TEXT NOT NULL, resource_id TEXT, details TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, status TEXT NOT NULL, action TEXT NOT NULL, confidence REAL NOT NULL, risk TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
      CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, user_id TEXT NOT NULL, task_type TEXT NOT NULL, model_id TEXT NOT NULL, input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL, cost REAL NOT NULL, latency_ms INTEGER NOT NULL, fallback_used INTEGER NOT NULL);
    """)
    return db

def audit(actor, event, resource_id=None, details=None):
    with connect() as db:
        db.execute("INSERT INTO audit(actor,event,resource_id,details) VALUES(?,?,?,?)", (actor,event,resource_id,json.dumps(details or {}, ensure_ascii=False)))

def audit_rows(user_id, reviewer=False, limit=100):
    with connect() as db:
        if reviewer: rows=db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else: rows=db.execute("SELECT * FROM audit WHERE actor=? ORDER BY id DESC LIMIT ?", (user_id,limit)).fetchall()
    return [dict(x) for x in rows]


def usage_rows(user_id, reviewer=False, limit=100):
    with connect() as db:
        if reviewer: rows=db.execute("SELECT * FROM usage ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else: rows=db.execute("SELECT * FROM usage WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id,limit)).fetchall()
    return [dict(x) for x in rows]
