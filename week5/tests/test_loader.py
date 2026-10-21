"""Tests for DocumentLoader and OCRProcessor (Day 2 requirements)."""

from __future__ import annotations
import sys
import unittest
from pathlib import Path

# Ensure week5 directory is on path
WEEK5_DIR = Path(__file__).resolve().parent.parent
if str(WEEK5_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK5_DIR))

from src.loader import DocumentLoader
from src.ocr import OCRProcessor
from src.schemas import DocumentContent

DOCS_DIR = WEEK5_DIR / "data" / "documents"


class TestDocumentLoader(unittest.TestCase):
    """Verifies that DocumentLoader handles text PDFs, scanned PDFs, images, and corrupt files."""

    def setUp(self):
        self.loader = DocumentLoader()
        self.ocr = OCRProcessor()

    def test_load_text_pdf(self):
        doc_path = DOCS_DIR / "doc_001.pdf"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        self.assertTrue(doc.is_valid)
        self.assertEqual(doc.doc_type, "pdf_text")
        self.assertGreater(len(doc.text), 40)
        self.assertEqual(doc.document_id, "doc_001")

    def test_load_scanned_pdf(self):
        doc_path = DOCS_DIR / "doc_026.pdf"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        self.assertTrue(doc.is_valid)
        self.assertEqual(doc.doc_type, "pdf_scanned")
        self.assertIsNotNone(doc.image_base64)
        self.assertGreater(len(doc.image_base64), 100)

    def test_load_png_image(self):
        doc_path = DOCS_DIR / "doc_036.png"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        self.assertTrue(doc.is_valid)
        self.assertEqual(doc.doc_type, "image_png")
        self.assertIsNotNone(doc.image_base64)

    def test_load_jpg_image(self):
        doc_path = DOCS_DIR / "doc_039.jpg"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        self.assertTrue(doc.is_valid)
        self.assertEqual(doc.doc_type, "image_jpg")
        self.assertIsNotNone(doc.image_base64)

    def test_load_blank_pdf(self):
        doc_path = DOCS_DIR / "doc_070_blank.pdf"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        # Should not crash
        self.assertTrue(doc.is_valid)
        self.assertEqual(doc.doc_type, "pdf_scanned")

    def test_load_corrupt_pdf_containment(self):
        doc_path = DOCS_DIR / "doc_069_corrupt.pdf"
        if not doc_path.exists():
            self.skipTest(f"Document {doc_path} not found")

        doc = self.loader.load_document(doc_path)
        self.assertFalse(doc.is_valid)
        self.assertEqual(doc.doc_type, "corrupt")
        self.assertIsNotNone(doc.error_message)

    def test_load_nonexistent_file(self):
        doc = self.loader.load_document("nonexistent_invoice_123.pdf")
        self.assertFalse(doc.is_valid)
        self.assertIn("File not found", doc.error_message)

    def test_ocr_processor_base64_roundtrip(self):
        from PIL import Image
        img = Image.new("RGB", (50, 50), color="white")
        b64 = self.ocr.encode_image_base64(img)
        self.assertIsInstance(b64, str)
        decoded = self.ocr.decode_base64_to_image(b64)
        self.assertEqual(decoded.size, (50, 50))


if __name__ == "__main__":
    unittest.main(verbosity=2)
