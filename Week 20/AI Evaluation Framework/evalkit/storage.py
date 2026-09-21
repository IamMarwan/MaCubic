"""Append-only run records with per-case checkpoints in SQLite."""
import json
import sqlite3
from pathlib import Path

class History:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL, manifest TEXT NOT NULL, summary TEXT);
          CREATE TABLE IF NOT EXISTS cases (run_id TEXT NOT NULL REFERENCES runs(id), case_id TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(run_id,case_id));
        ''')
    def start(self,manifest):
        with self.db:
            self.db.execute('INSERT INTO runs VALUES (?,?,?,?,NULL)',(manifest['run_id'],manifest['created_at'],'running',json.dumps(manifest)))
    def record(self,run_id,row):
        with self.db: self.db.execute('INSERT INTO cases VALUES (?,?,?)',(run_id,row['case_id'],json.dumps(row)))
    def finish(self,run_id,summary,status):
        with self.db: self.db.execute('UPDATE runs SET status=?,summary=? WHERE id=?',(status,json.dumps(summary),run_id))
    def list(self):
        return [dict(run_id=r[0],created_at=r[1],status=r[2],manifest=json.loads(r[3]),summary=json.loads(r[4]) if r[4] else None)
                for r in self.db.execute('SELECT * FROM runs ORDER BY created_at DESC')]
    def close(self): self.db.close()
