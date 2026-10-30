# Knowledge Service (Role A)

Document ingestion, OCR extraction, vector retrieval, and policy Q&A service built with FastAPI, ChromaDB, and Neon PostgreSQL.

## Overview

- **Corpus**: 50 corporate policy PDFs across Susan Electricals, Jayaswal Neco, Reckitt, Google, and GitLab.
- **Extraction & OCR**: `pypdf` for native text layers with `pypdfium2` + `RapidOCR` fallback for scanned pages (`extraction.py`).
- **Storage**: Local ChromaDB (`all-MiniLM-L6-v2` embeddings) and Neon PostgreSQL (`rag_documents` and `rag_chat_logs`).
- **Retrieval**: Page-bounded 500-character chunks (75-character overlap), multi-query expansion, and Reciprocal Rank Fusion (`rag_engine.py`).

## Project Layout

```text
knowledge_service/
├── app.py                      # FastAPI service (/search, /chat, /documents, /stats, /health)
├── mock_search_service.py      # Day 1 mock /search endpoint
├── contracts.py                # Request and response Pydantic schemas
├── rag_engine.py               # Retrieval, rank fusion, and chat orchestration
├── neon_client.py              # Neon PostgreSQL HTTP SQL client
├── extraction.py               # PDF text extraction and OCR fallback
├── ingestion_pipeline.py       # Batch ingestion into ChromaDB and Neon
├── retrieval_pipeline.py       # CLI retrieval script
├── answer_generation.py        # CLI answer generation script
├── evaluate_e2e.py             # End-to-end API test script
├── eval/
│   ├── chunk_size_eval.py      # Chunk size comparison script (500/75 vs 1000/150)
│   └── EVAL_REPORT.md          # Evaluation results
├── static/
│   └── index.html              # Web UI
└── data/
    ├── documents/              # 50 corporate policy PDFs
    ├── documents_metadata.json # Document metadata catalog
    ├── ingestion_report.json   # Extraction summary report
    └── test_questions.json     # 15 benchmark questions
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` in `knowledge_service/.env`:
```ini
DATABASE_URL=postgresql://user:password@endpoint.neon.tech/neondb?sslmode=require
```

## Running the Pipelines

### 1. Document Extraction & Ingestion
```bash
python ingestion_pipeline.py
```

### 2. Chunk Size Evaluation
```bash
python eval/chunk_size_eval.py
```

### 3. CLI Retrieval & Answer Generation
```bash
python retrieval_pipeline.py "What is the policy for reporting sexual harassment under POSH?"
python answer_generation.py "What are the rules regarding gifts and anti-bribery?"
```

### 4. Start the API Server
```bash
python app.py
```
- Web UI: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

### 5. Run End-to-End Tests
```bash
python evaluate_e2e.py
```
