# Day 3 — Session 4: Full Production RAG Pipeline

A production-grade, two-stage Retrieval-Augmented Generation (RAG) system built strictly according to the canonical 4-stage pipeline:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  INGESTION   │ ──► │  RETRIEVAL   │ ──► │   RERANKER   │ ──► │     LLM      │
│(ingestion.py)│     │(retrieval.py)│     │(reranker.py) │     │   (llm.py)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       ▲                                                              │
       └──────────────────── PIPELINE ORCHESTRATOR ───────────────────┘
                               (pipeline.py)
```

---

## 🏗️ Canonical Pipeline Architecture

```
day_03/session_4/
├── .env                       # API credentials & model configurations
├── requirements.txt           # chromadb, sentence-transformers, openai, numpy, pypdf
├── chroma_db/                 # Persistent on-disk vector database
├── docs/                      # 3 Enterprise Multi-Page Technical & Business PDFs
│   ├── cloud_platform_sla.pdf          (3 pages, SLA uptime tiers, penalties, RTO/RPO)
│   ├── employee_travel_policy.pdf      (3 pages, Flight classes, per diem, SOS hotline)
│   └── database_migration_guide.pdf    (3 pages, CDC replication, Kafka, rollback triggers)
│
├── 1. ingestion.py            # STAGE 1: Loads PDFs, chunks text, embeds, stores in Chroma
├── 2. retrieval.py            # STAGE 2: Bi-Encoder vector search fetches Top-K candidates
├── 3. reranker.py             # STAGE 3: Cross-Encoder token-level self-attention re-scorer
├── 4. llm.py                  # STAGE 4: Context Injection, Grounding prompt & Cited synthesis
├── 5. pipeline.py             # Master End-to-End Orchestrator connecting all 4 stages
│
├── qa_bot.py                  # Interactive CLI Bot & automated benchmark runner
├── main.py                    # Master demonstration of the 4-stage pipeline
└── README.md                  # Comprehensive architectural guide
```

---

## 🔬 The 4 Pipeline Stages Explained

### 1. Ingestion (`ingestion.py`)
- **Document Loading**: Reads PDFs page-by-page via `pypdf`, preserving `source`, `page`, and character counts.
- **Recursive Chunking**: Splits text into 300-token chunks with 50-token overlap to maintain sentence boundaries.
- **Vector Embedding**: Embeds chunks using Google Gemini's `gemini-embedding-001` (3072 dimensions) with disk caching.
- **Storage**: Upserts chunks idempotently into a persistent Chroma collection (`./chroma_db`).

### 2. Retrieval (`retrieval.py`)
- **Query Embedding**: Embeds incoming user questions with `gemini-embedding-001`.
- **Bi-Encoder Vector Search**: Searches Chroma via HNSW cosine distance in < 5ms.
- **Candidate Assembly**: Returns structured `CandidatePassage` objects (default: Top-6 candidates).

### 3. Reranker (`reranker.py`)
- **Bi-Encoder Limitation**: Bi-encoders compress 300 words into a single vector, losing token-to-token cross-attention.
- **Cross-Encoder Power**: Feeds `[CLS] Query [SEP] Passage [SEP]` through `cross-encoder/ms-marco-MiniLM-L-6-v2`. Every query word attends to every document word.
- **Re-ordering**: Calculates logit scores and sigmoid probabilities, re-ranking the most accurate passage to Rank #1.

### 4. Context Injection & Grounded LLM (`llm.py`)
- **Context Injection**: Tags each reranked excerpt with explicit document provenance:
  `[DOCUMENT EXCERPT: <filename> | Page: <page> | Chunk: <chunk_id>]`
- **Grounding Rules**: Enforces strict enterprise rules:
  1. Rely exclusively on provided facts (zero speculation).
  2. Every single claim must cite `[Source: <filename>, Page: <page>]`.
  3. If missing, say: *"The documentation does not provide details regarding [topic]."*.
- **Cited Synthesis**: Calls `gemini-3.5-flash-lite` to produce a structured answer and parses citations using regex.

---

## 🛡️ Relevance Guard: Handling "No-Relevant-Results"

When an out-of-domain question is asked (e.g. *"How do you bake sourdough bread?"*):
* Naive RAG systems blindly feed the closest vectors to the LLM, prompting hallucinations.
* Our `RAGPipeline` inspects the top Cross-Encoder logit score:
  ```python
  if top_rerank_score < RELEVANCE_THRESHOLD:  # default: -2.5
      return RAGQueryResult.refusal(
          "I am sorry, but the provided enterprise documentation does not contain "
          "information relevant to answer your question."
      )
  ```
* Sourdough bread scored **-11.09**, immediately triggering a safe refusal before reaching the LLM!

---

## 🚀 Execution Commands

```bash
# 1. Run the complete Ingestion -> Retrieval -> Reranker -> LLM walkthrough
python main.py

# 2. Start the interactive Q&A Bot (chat in real-time with your PDFs)
python qa_bot.py --interactive

# 3. Run automated 8-question benchmark (6 in-domain + 2 out-of-domain)
python qa_bot.py

# 4. Test individual stages in complete isolation:
python ingestion.py
python retrieval.py
python reranker.py
python llm.py
python pipeline.py
```
