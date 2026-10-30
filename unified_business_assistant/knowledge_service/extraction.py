import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pypdf import PdfReader

MIN_TEXT_CHARS = 20
OCR_RENDER_SCALE = 2.5

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCS_DIR = os.path.join(_HERE, "data", "documents")
DEFAULT_META_PATH = os.path.join(_HERE, "data", "documents_metadata.json")
OCR_CACHE_PATH = os.path.join(_HERE, "data", "ocr_cache.json")
REPORT_PATH = os.path.join(_HERE, "data", "ingestion_report.json")


@dataclass
class PageText:
    doc_id: str
    source: str
    page: int
    text: str
    method: str
    title: str
    company: str
    category: str


@dataclass
class DocReport:
    source: str
    doc_id: str
    pages: int = 0
    text_layer_pages: int = 0
    ocr_pages: int = 0
    failed_pages: List[int] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict


_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _ocr_engine = RapidOCR()
    return _ocr_engine


def _ocr_page(pdf_path: str, page_index0: int) -> str:
    import numpy as np
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    try:
        page = pdf[page_index0]
        bitmap = page.render(scale=OCR_RENDER_SCALE)
        img = np.array(bitmap.to_pil().convert("RGB"))
    finally:
        pdf.close()

    result, _ = _get_ocr()(img)
    if not result:
        return ""
    lines = [row[1] for row in result if row and len(row) >= 2 and str(row[1]).strip()]
    return "\n".join(lines).strip()


def _load_cache() -> Dict[str, str]:
    if os.path.exists(OCR_CACHE_PATH):
        try:
            with open(OCR_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: Dict[str, str]) -> None:
    tmp = OCR_CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp, OCR_CACHE_PATH)


def _cache_key(path: str, page: int) -> str:
    st = os.stat(path)
    return f"{os.path.basename(path)}|{st.st_size}|{int(st.st_mtime)}|{page}"


def load_metadata(meta_path: str = DEFAULT_META_PATH) -> Dict[str, dict]:
    if not os.path.exists(meta_path):
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        return {d["filename"]: d for d in json.load(f).get("documents", [])}


def extract_all(
    docs_dir: str = DEFAULT_DOCS_DIR,
    meta_path: str = DEFAULT_META_PATH,
    enable_ocr: bool = True,
    verbose: bool = True,
    write_report: bool = True,
):
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")
    meta = load_metadata(meta_path)
    files = sorted(f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf"))
    if not files:
        raise FileNotFoundError(f"No PDF files in {docs_dir}")

    cache = _load_cache()
    cache_dirty = False
    pages: List[PageText] = []
    reports: List[DocReport] = []

    for idx, fname in enumerate(files, 1):
        path = os.path.join(docs_dir, fname)
        info = meta.get(fname, {})
        doc_id = info.get("id", f"doc_{idx:03d}")
        title = info.get("title", os.path.splitext(fname)[0])
        company = info.get("company", "Unknown")
        category = info.get("category", "Uncategorized")
        rep = DocReport(source=fname, doc_id=doc_id)

        try:
            reader = PdfReader(path)
        except Exception as e:
            rep.error = f"PDF parse error: {e}"
            reports.append(rep)
            if verbose:
                print(f"Parse error in {fname}: {e}")
            continue

        rep.pages = len(reader.pages)
        for p_idx, page in enumerate(reader.pages, 1):
            try:
                text = (page.extract_text() or "").strip()
            except Exception:
                text = ""
            method = "text_layer"

            if len(text) < MIN_TEXT_CHARS and enable_ocr:
                key = _cache_key(path, p_idx)
                if key in cache:
                    ocr_text = cache[key]
                else:
                    try:
                        ocr_text = _ocr_page(path, p_idx - 1)
                    except Exception as e:
                        ocr_text = ""
                        if verbose:
                            print(f"OCR error on {fname} p{p_idx}: {e}")
                    cache[key] = ocr_text
                    cache_dirty = True
                    if verbose:
                        print(f"OCR {fname} p{p_idx}: {len(ocr_text)} chars")
                if len(ocr_text) >= MIN_TEXT_CHARS:
                    text, method = ocr_text, "ocr"

            if len(text) < MIN_TEXT_CHARS:
                rep.failed_pages.append(p_idx)
                continue

            if method == "ocr":
                rep.ocr_pages += 1
            else:
                rep.text_layer_pages += 1
            pages.append(PageText(doc_id, fname, p_idx, text, method, title, company, category))

        reports.append(rep)
        if cache_dirty and idx % 3 == 0:
            _save_cache(cache)
            cache_dirty = False

    if cache_dirty:
        _save_cache(cache)

    if write_report:
        summary = {
            "documents": len(files),
            "total_pages": sum(r.pages for r in reports),
            "text_layer_pages": sum(r.text_layer_pages for r in reports),
            "ocr_pages": sum(r.ocr_pages for r in reports),
            "failed_pages": sum(len(r.failed_pages) for r in reports),
            "parse_errors": [r.source for r in reports if r.error],
            "per_document": [r.__dict__ for r in reports],
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        if verbose:
            print(
                f"Extracted {summary['documents']} docs ({summary['total_pages']} pages): "
                f"{summary['text_layer_pages']} text, {summary['ocr_pages']} OCR, "
                f"{summary['failed_pages']} skipped."
            )
    return pages, reports


def chunk_pages(pages: List[PageText], chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    out: List[Chunk] = []
    for pg in pages:
        for c_idx, part in enumerate(splitter.split_text(pg.text), 1):
            cid = f"{pg.doc_id}_p{pg.page}_c{c_idx:02d}"
            out.append(
                Chunk(
                    chunk_id=cid,
                    text=part,
                    metadata={
                        "doc_id": pg.doc_id,
                        "source": pg.source,
                        "page": pg.page,
                        "title": pg.title,
                        "company": pg.company,
                        "category": pg.category,
                        "chunk_id": cid,
                        "chunk_index": c_idx,
                        "extraction_method": pg.method,
                    },
                )
            )
    return out


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    extract_all()
    print(f"Saved report to {REPORT_PATH}")
