"""Standalone local HTTP service using the Python standard library."""

import base64
import binascii
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from app.agent import WorkflowAgent
from app.config import ROOT, Settings
from app.ingestion import read_document
from app.models import InputError, TASKS
from app.planner import make_planner
from app.repository import Repository
from app.tools import DocumentTools, TOOL_SPECS


class Service:
    def __init__(self, settings, planner=None):
        self.settings = settings
        self.repository = Repository(settings.database)
        self.tools = DocumentTools(self.repository, settings.knowledge_base)
        self.agent = WorkflowAgent(settings, self.repository, self.tools, planner or make_planner(settings))
        self.slots = threading.BoundedSemaphore(2)


class AgentHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, service, address=None):
        self.service = service
        super().__init__(address or (service.settings.host, service.settings.port), Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "DocumentWorkflowAgent/1.0"

    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, format, *args):
        # Request text may contain document names; keep console logs minimal.
        print(f"HTTP {self.command}", flush=True)

    @property
    def service(self):
        return self.server.service

    def send(self, status, data, content_type="application/json; charset=utf-8"):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # The completed run remains available in history.

    def do_GET(self):
        route = urlsplit(self.path)
        query = parse_qs(route.query)
        static = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/docs": "api.html"}
        if route.path in static:
            path = ROOT / "web" / static[route.path]
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            return self.send(200, path.read_bytes(), mime + "; charset=utf-8")
        if route.path == "/api/v1/health":
            return self.send(200, {"status": "ok", "provider": self.service.settings.provider,
                                   "model": self.service.settings.model if self.service.settings.provider == "openai" else None,
                                   "tools": len(TOOL_SPECS), "tasks": sorted(TASKS)})
        if route.path == "/api/v1/tools":
            return self.send(200, TOOL_SPECS)
        if route.path == "/openapi.json":
            return self.send(200, (ROOT / "docs" / "openapi.json").read_bytes())
        if route.path == "/api/v1/runs":
            try:
                limit, offset = int(query.get("limit", ["25"])[0]), int(query.get("offset", ["0"])[0])
                if not 1 <= limit <= 100 or offset < 0:
                    raise ValueError
            except ValueError:
                return self.send(400, {"error": "limit must be 1-100 and offset must be nonnegative."})
            return self.send(200, {"runs": self.service.repository.list_runs(limit, offset)})
        if route.path.startswith("/api/v1/runs/"):
            segments = route.path.removeprefix("/api/v1/runs/").split("/")
            if len(segments) > 2 or (len(segments) == 2 and segments[1] != "events"):
                return self.send(404, {"error": "Endpoint not found."})
            result = self.service.repository.get_run(segments[0])
            if result is None:
                return self.send(404, {"error": "Run not found."})
            return self.send(200, {"events": result["events"]} if len(segments) == 2 else result)
        if route.path == "/api/v1/samples":
            samples = sorted((ROOT / "data" / "samples").glob("*.txt"))
            return self.send(200, {"samples": [{"filename": p.name, "text": p.read_text(encoding="utf-8")} for p in samples]})
        self.send(404, {"error": "Endpoint not found."})

    def read_submission(self, query):
        if self.headers.get("Transfer-Encoding"):
            raise InputError("Chunked uploads are not supported; send Content-Length.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise InputError("Invalid Content-Length.") from None
        maximum = self.service.settings.max_upload_bytes * 4 // 3 + 16384
        if not 0 < length <= maximum:
            raise InputError("Request body is empty or exceeds the upload limit.")
        content = self.rfile.read(length)
        if len(content) != length:
            raise InputError("Incomplete request body.")
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type == "application/json":
            try:
                payload = json.loads(content)
            except (ValueError, UnicodeDecodeError):
                raise InputError("Request body must be valid UTF-8 JSON.") from None
            if not isinstance(payload, dict):
                raise InputError("JSON body must be an object.")
            if set(payload) - {"filename", "text", "content_base64", "task", "instruction"}:
                raise InputError("Unknown JSON request fields.")
            if ("text" in payload) == ("content_base64" in payload):
                raise InputError("Supply exactly one of text or content_base64.")
            filename = payload.get("filename", "")
            if "text" in payload:
                if not isinstance(payload["text"], str):
                    raise InputError("text must be a string.")
                content = payload["text"].encode("utf-8")
            else:
                try:
                    if not isinstance(payload["content_base64"], str):
                        raise ValueError
                    content = base64.b64decode(payload["content_base64"], validate=True)
                except (ValueError, binascii.Error):
                    raise InputError("content_base64 is invalid.") from None
            task, instruction = payload.get("task", "workflow"), payload.get("instruction", "")
        elif content_type in {"text/plain", "text/markdown", "application/pdf", "application/octet-stream"}:
            filename = query.get("filename", [""])[0]
            task, instruction = query.get("task", ["workflow"])[0], query.get("instruction", [""])[0]
        else:
            raise InputError("Use JSON or a raw text/PDF upload. Multipart uploads are not supported.")
        if not isinstance(task, str) or task not in TASKS:
            raise InputError("Unsupported task.")
        if not isinstance(instruction, str) or len(instruction) > 2000:
            raise InputError("instruction must be a string of at most 2000 characters.")
        return read_document(filename, content, self.service.settings), task, instruction

    def do_POST(self):
        route = urlsplit(self.path)
        if route.path not in {"/api/v1/runs", "/api/v1/documents/index"}:
            return self.send(404, {"error": "Endpoint not found."})
        # The UI is same-origin. Browser calls from other origins are rejected.
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            return self.send(403, {"error": "Cross-origin submissions are disabled."})
        if not self.service.slots.acquire(blocking=False):
            return self.send(429, {"error": "Two submissions are already running. Try again shortly."})
        try:
            document, task, instruction = self.read_submission(parse_qs(route.query))
            if route.path.endswith("/index"):
                return self.send(200, {"indexed": self.service.tools.index_document(document)})
            result = self.service.agent.run(document, task, instruction)
            return self.send(201, result)
        except InputError as exc:
            self.send(400, {"error": str(exc)})
        except TimeoutError:
            self.send(408, {"error": "Upload timed out."})
        except Exception:
            self.send(500, {"error": "Service error. Check the local service configuration."})
        finally:
            self.service.slots.release()


def main():
    settings = Settings.from_env()
    service = Service(settings)
    with AgentHTTPServer(service) as server:
        print(f"Document Workflow Agent | provider={settings.provider}")
        print(f"Dashboard: http://{settings.host}:{server.server_port}")
        print("Press Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping the server.")
