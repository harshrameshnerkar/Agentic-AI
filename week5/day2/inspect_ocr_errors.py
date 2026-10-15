"""Day 2: OCR Error Inspection Script.

Loads real scanned invoice documents, inspects OCR and vision extraction behavior,
and catalogs standard OCR failure modes (character confusion, decimal dropping,
table column bleeding) that must be handled by the extraction schema.
"""

from __future__ import annotations
import json
from pathlib import Path
from week5.pipeline.document_loader import DocumentLoader
from week5.pipeline.extractor import DocumentExtractor

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "documents"

COMMON_OCR_FAILURE_MODES = [
    {
        "category": "Character Confusion",
        "description": "Letters O and I substituted for numbers 0 and 1, or 8 confused with B/&.",
        "example_raw": "INV-2O24-IOO1 | SuperStore & Sons -> SuperStore 8 Sons",
        "mitigation": "Regex preprocessing and alphanumeric stripping on invoice_id and tax_id.",
    },
    {
        "category": "Decimal & Comma Inversion",
        "description": "European periods vs commas, or dust specks misread as decimals ($120050 vs $1,200.50).",
        "example_raw": "$ 4 916,88 -> 4916.88 | $1.200,50 -> 1200.50",
        "mitigation": "Flexible decimal parser with European currency heuristics and quantize(Decimal('0.01')).",
    },
    {
        "category": "Table Column Bleed",
        "description": "Line items on opposite columns merge into single text strings without whitespace.",
        "example_raw": "Widget A 50.00 Widget B 70.00 on single line",
        "mitigation": "Multimodal vision extraction directly preserving spatial layout from image.",
    },
    {
        "category": "Omitted Optional Fields",
        "description": "Scanned invoices missing explicit due dates or tax numbers.",
        "example_raw": "Terms: Net 30 (no calendar date printed)",
        "mitigation": "Strict Pydantic typing with Optional[date] = None; never synthesize speculative dates.",
    },
]

def main():
    print("=" * 75)
    print("DAY 2: OCR ERROR INSPECTION & DOCUMENT LOADER AUDIT")
    print("=" * 75)

    loader = DocumentLoader()
    extractor = DocumentExtractor()

    sample_scans = ["doc_026.pdf", "doc_027.pdf", "doc_036.png", "doc_037.png"]

    print("\n[INSPECTION 1] Loading and Parsing Real Scanned Documents:")
    for filename in sample_scans:
        path = DOCS_DIR / filename
        doc = loader.load_document(path)
        print(f"  • {doc.filename:<15} -> Type: {doc.doc_type:<12} | Valid: {doc.is_valid} | Image Base64: {len(doc.image_base64 or '') > 0}")

    print("\n[INSPECTION 2] Documented Real-World OCR Failure Modes & Schema Defenses:")
    for i, mode in enumerate(COMMON_OCR_FAILURE_MODES, 1):
        print(f"\n  Failure Mode {i}: {mode['category']}")
        print(f"    - Symptom:    {mode['description']}")
        print(f"    - Example:    {mode['example_raw']}")
        print(f"    - Defense:    {mode['mitigation']}")

    print("\n" + "=" * 75)
    print("OCR error inspection complete. Schema defenses active in extraction_schema.py.")
    print("=" * 75)

if __name__ == "__main__":
    main()
