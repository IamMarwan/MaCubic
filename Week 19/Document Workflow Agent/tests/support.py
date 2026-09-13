import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.config import Settings
from app.ingestion import read_document
from app.server import Service


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Settings(database=Path(self.temp.name) / "test.db")
        self.service = Service(self.settings)

    def doc(self, text, filename="test.txt"):
        return read_document(filename, text.encode("utf-8"), self.settings)

    def service_with(self, planner=None, **settings):
        return Service(replace(self.settings, **settings), planner=planner)


def small_pdf(lines):
    """A valid one-page text PDF fixture without an extra generation dependency."""
    operations = ["BT /F1 10 Tf 40 750 Td"]
    for index, line in enumerate(lines):
        if index:
            operations.append("0 -14 Td")
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        operations.append(f"({escaped}) Tj")
    operations.append("ET")
    stream = "\n".join(operations).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    result, offsets = bytearray(b"%PDF-1.4\n"), [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    startxref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode())
    return bytes(result)
