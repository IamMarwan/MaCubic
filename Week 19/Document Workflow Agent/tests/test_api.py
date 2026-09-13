import base64
import json
import threading
import urllib.error
import urllib.request

from app.server import AgentHTTPServer
from scripts.scenarios import BASE_DRAWING, drawing
from tests.support import ServiceTest


class APITests(ServiceTest):
    def setUp(self):
        super().setUp()
        self.server = AgentHTTPServer(self.service, ("127.0.0.1", 0))
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, payload=None, headers=None, raw=None):
        data = json.dumps(payload).encode() if payload is not None else raw
        request = urllib.request.Request(self.base + path, data=data,
                    headers=headers or {"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            content = response.read()
            if "application/json" in response.headers.get("Content-Type", ""):
                content = json.loads(content)
            return response.status, content

    def test_submit_then_retrieve_history_and_events(self):
        status, run = self.request("/api/v1/runs", {"filename": "drawing.txt", "text": drawing()})
        self.assertEqual(status, 201)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(self.request(f"/api/v1/runs/{run['id']}")[1], run)
        self.assertEqual(self.request(f"/api/v1/runs/{run['id']}/events")[1]["events"], run["events"])
        self.assertEqual(self.request("/api/v1/runs")[1]["runs"][0]["id"], run["id"])

    def test_raw_upload_and_basename_validation(self):
        status, run = self.request("/api/v1/runs?filename=..%2Fdrawing.txt&task=classify",
                                  raw=drawing().encode(), headers={"Content-Type": "text/plain"})
        self.assertEqual(status, 201)
        self.assertEqual(run["filename"], "drawing.txt")
        self.assertEqual(len(run["result"]["tools_used"]), 1)

    def test_base64_upload(self):
        status, run = self.request("/api/v1/runs", {"filename": "drawing.txt",
                                  "content_base64": base64.b64encode(drawing().encode()).decode(), "task": "summarize"})
        self.assertEqual(status, 201)
        self.assertEqual(run["result"]["tools_used"], ["generate_summary"])

    def test_invalid_json_schema_and_tasks(self):
        payloads = [[], {"filename": "a.txt", "text": "hello", "task": "delete"},
                    {"filename": "a.txt", "text": "hello", "content_base64": "aGVsbG8="},
                    {"filename": "a.txt", "content_base64": "@@@"},
                    {"filename": "a.txt", "text": "hello", "instruction": 123},
                    {"filename": "a.txt", "text": "hello", "unexpected": 1}]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(self.request("/api/v1/runs", payload)[0], 400)
        self.assertEqual(self.request("/api/v1/runs")[1]["runs"], [])

    def test_index_then_detect_old_revision(self):
        status, _ = self.request("/api/v1/documents/index", {"filename": "base.txt", "text": BASE_DRAWING})
        self.assertEqual(status, 200)
        _, run = self.request("/api/v1/runs", {"filename": "old.txt", "text": drawing(Revision="00"), "task": "revisions"})
        self.assertEqual(run["result"]["outputs"]["detect_previous_revisions"]["status"], "superseded")

    def test_index_requires_document_identity(self):
        self.assertEqual(self.request("/api/v1/documents/index", {"filename": "memo.txt", "text": "Site memo"})[0], 400)

    def test_unknown_run_and_invalid_pagination(self):
        self.assertEqual(self.request("/api/v1/runs/not-found")[0], 404)
        self.assertEqual(self.request("/api/v1/runs?limit=101")[0], 400)
        self.assertEqual(self.request("/api/v1/runs?offset=-1")[0], 400)

    def test_health_and_tool_catalog(self):
        self.assertEqual(self.request("/api/v1/health")[1]["provider"], "offline")
        self.assertEqual(len(self.request("/api/v1/tools")[1]), 8)

    def test_dashboard_and_documentation_routes(self):
        self.assertIn(b"Document Workflow Agent", self.request("/")[1])
        self.assertEqual(self.request("/docs")[0], 200)
        self.assertEqual(self.request("/openapi.json")[1]["openapi"], "3.1.0")
        self.assertEqual(self.request("/../../.env")[0], 404)

    def test_saturation_returns_429(self):
        self.service.slots.acquire()
        self.service.slots.acquire()
        try:
            self.assertEqual(self.request("/api/v1/runs", {"filename": "a.txt", "text": "hello"})[0], 429)
        finally:
            self.service.slots.release()
            self.service.slots.release()

    def test_cross_origin_submission_is_rejected(self):
        status, _ = self.request("/api/v1/runs", {"filename": "a.txt", "text": "hello"},
                                 headers={"Content-Type": "application/json", "Origin": "https://example.invalid"})
        self.assertEqual(status, 403)
