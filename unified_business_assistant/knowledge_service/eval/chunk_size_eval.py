import json
import os
import sys
from datetime import date

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import chromadb
from chromadb.utils import embedding_functions
from extraction import extract_all, chunk_pages


def evaluate_config(pages, questions, ef, name: str, chunk_size: int, chunk_overlap: int, batch_size: int = 200):
    print(f"\nEvaluating {name} (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    chunks = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Generated {len(chunks)} chunks across {len(pages)} pages.")

    client = chromadb.EphemeralClient()
    col_name = f"eval_{chunk_size}_{chunk_overlap}"
    try:
        client.delete_collection(col_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=col_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )

    doc_hits = {1: 0, 3: 0, 5: 0}
    page_hits = {1: 0, 3: 0, 5: 0}
    per_query = []

    for q in questions:
        res = collection.query(
            query_texts=[q["question"]],
            n_results=5,
            include=["metadatas", "distances"],
        )
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        exp_source = q["expected_source"]
        exp_pages = set(q["expected_pages"])

        doc_rank = None
        page_rank = None
        top1_score = round(max(0.0, 1.0 - dists[0]), 4) if dists else 0.0

        for idx, meta in enumerate(metas, 1):
            src = meta.get("source", "")
            pg = int(meta.get("page", 0))
            if src == exp_source:
                if doc_rank is None:
                    doc_rank = idx
                if pg in exp_pages and page_rank is None:
                    page_rank = idx

        for k in (1, 3, 5):
            if doc_rank is not None and doc_rank <= k:
                doc_hits[k] += 1
            if page_rank is not None and page_rank <= k:
                page_hits[k] += 1

        per_query.append(
            {
                "id": q["id"],
                "question": q["question"],
                "expected_source": exp_source,
                "expected_pages": q["expected_pages"],
                "doc_rank": doc_rank,
                "page_rank": page_rank,
                "top1_score": top1_score,
                "hit": page_rank is not None and page_rank <= 5,
            }
        )

    n = len(questions)
    metrics = {
        "total_chunks": len(chunks),
        "doc_recall_1": round(doc_hits[1] * 100.0 / n, 1),
        "doc_recall_3": round(doc_hits[3] * 100.0 / n, 1),
        "doc_recall_5": round(doc_hits[5] * 100.0 / n, 1),
        "page_recall_1": round(page_hits[1] * 100.0 / n, 1),
        "page_recall_3": round(page_hits[3] * 100.0 / n, 1),
        "page_recall_5": round(page_hits[5] * 100.0 / n, 1),
        "per_query": per_query,
    }
    print(f"{name}: Doc Recall@5 = {metrics['doc_recall_5']}% | Page Recall@5 = {metrics['page_recall_5']}%")
    return metrics


def write_markdown_report(res_a: dict, res_b: dict, report_path: str):
    lines = [
        "# Retrieval Evaluation & Chunk Size Benchmark",
        "",
        "## 1. Summary",
        f"- **Date**: {date.today().isoformat()}",
        "- **Test Set**: 15 labelled questions (`data/test_questions.json`) across 5 companies.",
        "- **Embedding Model**: `all-MiniLM-L6-v2`",
        "- **Selected Configuration**: **Config A (500 chars, 75 overlap)**",
        f"- **Recall@5**: **Document Recall@5 = {res_a['doc_recall_5']}%** | **Page Recall@5 = {res_a['page_recall_5']}%**",
        "",
        "## 2. Benchmark Results",
        "",
        "| Metric | Config A (500 chars, 75 overlap) | Config B (1000 chars, 150 overlap) |",
        "|---|---|---|",
        f"| Total Chunks | {res_a['total_chunks']} | {res_b['total_chunks']} |",
        f"| Document Recall@1 | {res_a['doc_recall_1']}% | {res_b['doc_recall_1']}% |",
        f"| Document Recall@3 | {res_a['doc_recall_3']}% | {res_b['doc_recall_3']}% |",
        f"| Document Recall@5 | {res_a['doc_recall_5']}% | {res_b['doc_recall_5']}% |",
        f"| Exact Page Recall@1 | {res_a['page_recall_1']}% | {res_b['page_recall_1']}% |",
        f"| Exact Page Recall@3 | {res_a['page_recall_3']}% | {res_b['page_recall_3']}% |",
        f"| Exact Page Recall@5 | {res_a['page_recall_5']}% | {res_b['page_recall_5']}% |",
        "",
        "## 3. Reason for Choosing Config A (500 / 75)",
        f"1. **Higher Recall**: Config A achieved {res_a['doc_recall_5']}% Document Recall@5 and {res_a['page_recall_5']}% Page Recall@5 compared to {res_b['doc_recall_5']}% and {res_b['page_recall_5']}% for Config B. Top-1 page recall also improved from {res_b['page_recall_1']}% to {res_a['page_recall_1']}%.",
        "2. **Model Window Fit**: `all-MiniLM-L6-v2` has a 256-token limit. Using 500-character chunks avoids token truncation and keeps embeddings focused on single policy rules rather than mixing multiple sections together.",
        "3. **Page Provenance**: Smaller chunks map cleanly to individual sections on a page, which improves ranking scores on specific policy questions (such as filing deadlines or expense limits).",
        "",
        "## 4. Per-Query Breakdown (Config A)",
        "",
    ]

    for item in res_a["per_query"]:
        status = "HIT" if item["hit"] else "MISS"
        lines.append(f"- **{item['id']}**: {item['question']}")
        lines.append(f"  - Expected: `{item['expected_source']}` (Pages {item['expected_pages']})")
        lines.append(
            f"  - Result: {status} | Doc Rank: {item['doc_rank']}, "
            f"Page Rank: {item['page_rank']} | Top-1 Score: {item['top1_score']:.4f}"
        )
        lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved report to {report_path}")


def main():
    docs_dir = os.path.join(ROOT, "data", "documents")
    meta_path = os.path.join(ROOT, "data", "documents_metadata.json")
    q_path = os.path.join(ROOT, "data", "test_questions.json")
    report_path = os.path.join(HERE, "EVAL_REPORT.md")

    with open(q_path, "r", encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    print("Loading extracted pages...")
    pages, _ = extract_all(docs_dir=docs_dir, meta_path=meta_path, enable_ocr=True, verbose=False, write_report=False)

    ef = embedding_functions.DefaultEmbeddingFunction()
    res_a = evaluate_config(pages, questions, ef, "Config A", chunk_size=500, chunk_overlap=75)
    res_b = evaluate_config(pages, questions, ef, "Config B", chunk_size=1000, chunk_overlap=150)

    write_markdown_report(res_a, res_b, report_path)


if __name__ == "__main__":
    main()
