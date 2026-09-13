import io
from dataclasses import replace

from app.ingestion import read_document
from app.models import InputError, State
from app.tools import extract_fields, revision_key
from scripts.scenarios import drawing
from tests.support import ServiceTest, small_pdf


class IngestionAndToolTests(ServiceTest):
    def test_empty_binary_and_unsupported_inputs(self):
        for name, data in [("a.txt", b""), ("a.txt", b"\x00"), ("a.txt", b"\xff"), ("a.exe", b"hello"), ("a.pdf", b"not PDF")]:
            with self.subTest(name=name, data=data), self.assertRaises(InputError):
                read_document(name, data, self.settings)

    def test_size_and_text_limits(self):
        with self.assertRaises(InputError):
            read_document("a.txt", b"a" * 11, replace(self.settings, max_upload_bytes=10))
        with self.assertRaises(InputError):
            read_document("a.txt", b"a" * 11, replace(self.settings, max_text_chars=10))

    def test_filename_is_basename_only(self):
        document = read_document("../../private/test.txt", b"hello", self.settings)
        self.assertEqual(document.filename, "test.txt")

    def test_text_pdf_is_extracted(self):
        doc = read_document("drawing.pdf", small_pdf(drawing().splitlines()), self.settings)
        self.assertIn("DT-STR-101", doc.text)
        self.assertEqual(doc.pages, 1)
        result = self.service.agent.run(doc)
        self.assertEqual(result["status"], "completed")

    def test_blank_and_encrypted_pdf_are_rejected(self):
        from pypdf import PdfWriter
        for encrypted in (False, True):
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            if encrypted:
                writer.encrypt("test-password")
            buffer = io.BytesIO()
            writer.write(buffer)
            with self.subTest(encrypted=encrypted), self.assertRaises(InputError):
                read_document("blank.pdf", buffer.getvalue(), self.settings)

    def test_mixed_pdf_does_not_silently_skip_scanned_pages(self):
        from pypdf import PdfReader, PdfWriter
        writer = PdfWriter()
        writer.add_page(PdfReader(io.BytesIO(small_pdf(["Document Type: Invoice"])) ).pages[0])
        writer.add_blank_page(width=100, height=100)
        buffer = io.BytesIO()
        writer.write(buffer)
        with self.assertRaisesRegex(InputError, "page 2"):
            read_document("mixed.pdf", buffer.getvalue(), self.settings)

    def test_placeholder_field_is_missing(self):
        fields = extract_fields(self.doc(drawing(**{"Checked By": "TBD"})))
        self.assertNotIn("checked_by", fields["fields"])

    def test_conflicting_values_are_not_guessed(self):
        metadata = extract_fields(self.doc(drawing() + "Project: Different Project\n"))
        self.assertNotIn("project", metadata["fields"])
        self.assertEqual(len(metadata["evidence"]["project"]), 2)
        self.assertEqual(metadata["conflicts"]["project"], ["Demo Tower", "Different Project"])

    def test_numeric_and_prefixed_revision_order(self):
        self.assertLess(revision_key("02"), revision_key("10"))
        self.assertLess(revision_key("P02"), revision_key("P10"))
        self.assertLess(revision_key("Z"), revision_key("AA"))
        self.assertIsNone(revision_key("A/B"))

    def test_newer_revision_10_is_not_sorted_before_2(self):
        self.service.tools.index_document(self.doc(drawing(Revision="10")))
        result = self.service.agent.run(self.doc(drawing(Revision="2")), "revisions")
        self.assertEqual(result["result"]["outputs"]["detect_previous_revisions"]["status"], "superseded")

    def test_ambiguous_declared_type_is_unknown(self):
        state = State(self.doc("Document Type: Shop Drawing and Invoice\n"), "classify")
        result = self.service.tools.classify_document(state)
        self.assertEqual(result["document_type"], "unknown")
        self.assertTrue(result["ambiguous"])

    def test_body_reference_does_not_override_heading(self):
        state = State(self.doc(drawing() + "Please attach the supplier invoice.\n"), "classify")
        self.assertEqual(self.service.tools.classify_document(state)["document_type"], "drawing")

    def test_missing_revision_is_explicitly_not_checkable(self):
        result = self.service.agent.run(self.doc(drawing(Revision=None)), "revisions")
        self.assertEqual(result["result"]["outputs"]["detect_previous_revisions"]["status"], "not_checkable")

    def test_search_has_cited_matches_and_handles_no_match(self):
        state = State(self.doc(drawing()), "workflow")
        state.results["classify_document"] = self.service.tools.classify_document(state)
        state.results["extract_metadata"] = extract_fields(state.document)
        match = self.service.tools.search_knowledge_base(state, query="structural slab drawing")
        self.assertEqual(match["matches"][0]["id"], "DEMO-DWG-001")
        self.assertEqual(self.service.tools.search_knowledge_base(state, query="zxqv12345")["matches"], [])
