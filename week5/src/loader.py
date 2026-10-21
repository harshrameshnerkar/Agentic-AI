"""Multi-Modal Document Loader for Document Extraction Pipeline.

Handles:
1. Vector Text PDFs (pdf_text): Direct font stream extraction via pdfplumber.
2. Scanned PDFs (pdf_scanned): Detects raster/image-only PDFs, renders pages via pypdfium2 / OCRProcessor.
3. Raster Images (image_png, image_jpg): Preprocesses and base64 encodes for multimodal vision.
4. Stress / Corrupt Files: Graceful error containment (zero unhandled crashes).
"""

from __future__ import annotations
import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from PIL import Image
import pdfplumber
import pypdf
import pypdfium2

from src.ocr import OCRProcessor
from src.schemas import DocType, DocumentContent


class DocumentLoader:
    """Universal multi-modal invoice loader with zero-crash guarantees."""

    def __init__(self, render_scale: float = 2.0, ocr_fallback: bool = True):
        self.render_scale = render_scale
        self.ocr_fallback = ocr_fallback
        self.ocr_processor = OCRProcessor()

    def load_document(self, file_path: Union[str, Path]) -> DocumentContent:
        """Loads and parses any invoice document file without raising unhandled exceptions."""
        path = Path(file_path).resolve()
        filename = path.name
        doc_id = path.stem

        if not path.exists():
            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="corrupt",
                text="",
                is_valid=False,
                error_message=f"File not found: {path}",
            )

        suffix = path.suffix.lower()

        # Handle Image formats directly
        if suffix in (".png", ".jpg", ".jpeg", ".webp"):
            return self._load_image(path, doc_id, filename, suffix)

        # Handle PDF formats
        if suffix == ".pdf":
            return self._load_pdf(path, doc_id, filename)

        return DocumentContent(
            document_id=doc_id,
            filename=filename,
            file_path=path,
            doc_type="unknown",
            text="",
            is_valid=False,
            error_message=f"Unsupported file format: {suffix}",
        )

    def _load_image(self, path: Path, doc_id: str, filename: str, suffix: str) -> DocumentContent:
        doc_type: DocType = "image_png" if suffix == ".png" else "image_jpg"
        try:
            with Image.open(path) as img:
                img.verify()

            # Reopen after verify() to read bytes and check OCR text
            with Image.open(path) as img:
                b64_data = self.ocr_processor.encode_image_base64(img, format="PNG" if suffix == ".png" else "JPEG")
                ocr_text = self.ocr_processor.extract_text_from_image(img) if self.ocr_fallback else ""

            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type=doc_type,
                text=ocr_text,
                image_base64=b64_data,
                page_count=1,
                is_valid=True,
            )
        except Exception as e:
            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="corrupt",
                text="",
                is_valid=False,
                error_message=f"Corrupt image file: {e}",
            )

    def _load_pdf(self, path: Path, doc_id: str, filename: str) -> DocumentContent:
        # First check if PDF is corrupt / unreadable
        try:
            reader = pypdf.PdfReader(str(path))
            page_count = len(reader.pages)
            if page_count == 0:
                return DocumentContent(
                    document_id=doc_id,
                    filename=filename,
                    file_path=path,
                    doc_type="corrupt",
                    text="",
                    page_count=0,
                    is_valid=False,
                    error_message="Empty PDF with 0 pages",
                )
        except Exception as e:
            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="corrupt",
                text="",
                is_valid=False,
                error_message=f"Corrupt PDF header/stream: {e}",
            )

        # Attempt vector text extraction via pdfplumber
        extracted_text = ""
        try:
            with pdfplumber.open(path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t.strip())
                extracted_text = "\n\n".join(pages_text).strip()
        except Exception:
            extracted_text = ""

        # Check if text is sufficient (Text PDF)
        if len(extracted_text) >= 40:
            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="pdf_text",
                text=extracted_text,
                page_count=page_count,
                is_valid=True,
            )

        # Scanned PDF or Blank page: Render page 0 via pypdfium2 into high-res bitmap
        try:
            pdf_doc = pypdfium2.PdfDocument(str(path))
            if len(pdf_doc) == 0:
                return DocumentContent(
                    document_id=doc_id,
                    filename=filename,
                    file_path=path,
                    doc_type="pdf_scanned",
                    text="",
                    page_count=0,
                    is_valid=False,
                    error_message="Blank PDF with 0 pages in pypdfium2",
                )

            page = pdf_doc[0]
            bitmap = page.render(scale=self.render_scale)
            pil_image = bitmap.to_pil()

            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

            # Check if image is completely blank (white/black)
            is_blank = self._is_image_blank(pil_image)

            # If OCR enabled, try extracting text from scanned bitmap
            ocr_text = self.ocr_processor.extract_text_from_image(pil_image) if self.ocr_fallback else ""
            combined_text = extracted_text if extracted_text else ocr_text

            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="pdf_scanned",
                text=combined_text,
                image_base64=b64_img,
                page_count=page_count,
                is_valid=True,
                error_message="Blank page detected" if is_blank else None,
            )
        except Exception as e:
            return DocumentContent(
                document_id=doc_id,
                filename=filename,
                file_path=path,
                doc_type="corrupt",
                text="",
                page_count=page_count,
                is_valid=False,
                error_message=f"Failed to render scanned PDF: {e}",
            )

    @staticmethod
    def _is_image_blank(img: Image.Image, threshold: float = 0.995) -> bool:
        """Heuristic to detect completely blank/uniform scanned pages."""
        try:
            gray = img.convert("L")
            extrema = gray.getextrema()
            if extrema[0] == extrema[1]:
                return True
            hist = gray.histogram()
            dominant_pixel_ratio = max(hist) / float(img.width * img.height)
            return dominant_pixel_ratio >= threshold
        except Exception:
            return False
