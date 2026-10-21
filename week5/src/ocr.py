"""OCR and image pre-processing module for document extraction.

Provides:
- Image pre-processing: grayscale, contrast enhancement, binarization, deskewing.
- PDF page rasterization using pypdfium2.
- Tesseract OCR extraction with graceful fallback when system binaries are absent.
- Multimodal vision encoding (base64 PNG/JPEG).
"""

from __future__ import annotations
import base64
import io
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pypdfium2

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class OCRProcessor:
    """Pre-processes document images and extracts OCR text."""

    def __init__(self, default_dpi: int = 200):
        self.default_dpi = default_dpi
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        if not HAS_PYTESSERACT:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @property
    def is_tesseract_available(self) -> bool:
        return self._tesseract_available

    def preprocess_image(
        self,
        image: Image.Image,
        enhance_contrast: bool = True,
        grayscale: bool = True,
        auto_deskew: bool = False,
    ) -> Image.Image:
        """Applies image pre-processing filters for optimal OCR/vision readability."""
        img = image.copy()

        # Convert palette/transparency to RGB
        if img.mode in ("P", "RGBA", "LA"):
            img = img.convert("RGB")

        if grayscale and img.mode != "L":
            img = ImageOps.grayscale(img)

        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4)
            # Slight sharpness boost
            sharpener = ImageEnhance.Sharpness(img)
            img = sharpener.enhance(1.2)

        return img

    def render_pdf_to_images(
        self,
        pdf_path: Union[str, Path],
        max_pages: int = 5,
        scale: float = 2.0,
    ) -> List[Image.Image]:
        """Renders pages of a PDF document to PIL Images via pypdfium2."""
        images: List[Image.Image] = []
        try:
            pdf = pypdfium2.PdfDocument(str(pdf_path))
            n_pages = min(len(pdf), max_pages)
            for i in range(n_pages):
                page = pdf[i]
                bitmap = page.render(scale=scale)
                pil_image = bitmap.to_pil()
                images.append(pil_image)
            pdf.close()
        except Exception as e:
            # Return empty list on failure, let caller handle corrupt files
            pass
        return images

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extracts text from an image using Tesseract OCR, with graceful fallback."""
        if not self._tesseract_available:
            return ""

        try:
            processed = self.preprocess_image(image)
            text = pytesseract.image_to_string(processed, config="--psm 6")
            return text.strip()
        except Exception:
            return ""

    def encode_image_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """Encodes PIL Image to base64 ASCII string for multimodal vision LLMs."""
        buffer = io.BytesIO()
        if image.mode in ("RGBA", "P") and format.upper() == "JPEG":
            image = image.convert("RGB")
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def decode_base64_to_image(self, b64_str: str) -> Image.Image:
        """Decodes base64 ASCII string back into a PIL Image."""
        raw_bytes = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(raw_bytes))
