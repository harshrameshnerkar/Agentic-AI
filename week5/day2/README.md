# Day 2: Parsing & The Extraction Schema

> **Task 5: Document Extraction Pipeline**  
> **Track:** Generative AI  
> **Core Focus:** Building a multi-modal document loader resilient to text PDFs, scanned PDFs, images, blank pages, and corrupted files, plus defining a canonical 11-field Pydantic V2 schema with real types (`datetime.date`, `decimal.Decimal`, `Enum`) and automated validation retries.

---

## 1. Executive Summary & Deliverables

In production financial document extraction, pipelines frequently crash due to format heterogeneity, malformed binary files, and loose schema typing. On Day 2, we established:

1. **Multi-Modal Document Loader ([`document_loader.py`](../pipeline/document_loader.py)):**
   - **Text PDFs:** Uses `pdfplumber` to extract native vector font streams.
   - **Scanned PDFs:** Uses `pypdfium2` to render 200 DPI bitmap images when font streams are absent.
   - **Images:** Loads PNG, JPG, and JPEG files into base64 visual containers.
   - **Crash Protection:** Traps unhandled file read exceptions, corrupt PDF headers (`doc_069_corrupt.pdf`), and empty pages (`doc_070_blank.pdf`) without crashing.
2. **Canonical Typed Schema ([`extraction_schema.py`](../pipeline/extraction_schema.py)):**
   - **Dates as `datetime.date`:** Rejects impossible dates (e.g. `2024-02-30`) with `ValidationError`.
   - **Amounts as `decimal.Decimal`:** Eliminates IEEE-754 binary floating-point rounding bugs (`0.1 + 0.2 != 0.3`).
   - **Enums for Domain Codes:** Maps currency symbols (`$`, `€`) to `CurrencyEnum` and payment terms to `PaymentTermsEnum`.
3. **Structured Extractor with Retry Loop ([`extractor.py`](../pipeline/extractor.py)):**
   - Binds Pydantic validation into the model response loop; on schema violation, catches the error and reprompts the model to fix the invalid fields (up to 3 retries).
4. **OCR Error Catalog ([`inspect_ocr_errors.py`](inspect_ocr_errors.py)):**
   - Documents real-world OCR failure modes (character confusion, decimal inversion, table bleed) and the schema defenses implemented.

---

## 2. Verification & Execution

Run the Day 2 Acceptance Verification Suite:
```bash
python week5/day2/verify_day2.py
```

Run the OCR Error Inspection Audit:
```bash
python week5/day2/inspect_ocr_errors.py
```
