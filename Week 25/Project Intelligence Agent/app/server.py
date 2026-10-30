from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from hmac import compare_digest

from app.agent import ProjectAgent

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 16_384


class Handler(BaseHTTPRequestHandler):
    server_version = "ProjectIntelligenceDemo/1.0"

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._json(404, {"error": "not_found"})
            return
        self._json(200, {"status": "ok", "service": "Project Intelligence Agent"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/investigate":
            self._json(404, {"error": "not_found"})
            return
        expected = os.environ.get("PROJECT_AGENT_TOKEN")
        if expected:
            supplied = self.headers.get("Authorization", "")
            if not supplied.startswith("Bearer ") or not compare_digest(supplied[7:], expected):
                self._json(401, {"error": "unauthorized"})
                return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "invalid_content_length"})
            return
        if length < 1 or length > MAX_BODY:
            self._json(413 if length > MAX_BODY else 400, {"error": "invalid_body_size", "max_bytes": MAX_BODY})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json(400, {"error": "invalid_json"})
            return
        request = payload.get("request") if isinstance(payload, dict) else None
        if not isinstance(request, str) or not request.strip() or len(request) > 2000:
            self._json(400, {"error": "request_must_be_1_to_2000_characters"})
            return
        result = ProjectAgent(ROOT / "data" / "project.json").investigate(request.strip())
        self._json(200, result)

    def log_message(self, fmt: str, *args) -> None:
        # Avoid logging user-supplied request text or authorization headers.
        print(f"{self.log_date_time_string()} {self.command} {self.path} {args[1] if len(args) > 1 else ''}")


def serve() -> None:
    host = os.environ.get("PROJECT_AGENT_HOST", "127.0.0.1")
    port = int(os.environ.get("PROJECT_AGENT_PORT", "8080"))
    print(f"Serving on http://{host}:{port} (Ctrl+C to stop)")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
