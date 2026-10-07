# Day 3 — Session 2: Chunking & Ingestion

A production-grade, modular RAG ingestion pipeline demonstrating document loading, token-aware recursive text splitting, metadata preservation, and an empirical evaluation comparing **300-token** vs. **800-token** chunk retrieval.

---

## 🎯 Learning Objectives

1. **Document Loading**:
   - Ingesting multi-page PDFs using `pypdf`.
   - Structural patterns for ingesting DOCX (`python-docx`) and Web Pages (`BeautifulSoup` / `WebBaseLoader`).
2. **Chunking Strategies**:
   - **Fixed-size chunking**: Fixed character/token slicing (breaks words/sentences).
   - **Recursive Character chunking**: Delimiter hierarchy `["\n\n", "\n", ". ", " ", ""]` to preserve natural paragraphs and sentences.
   - **Semantic chunking**: Sentence embedding distance to detect natural topic transitions.
3. **Chunk Size & Overlap Trade-offs**:
   - **300 Tokens (Small)**: Laser-focused semantic embeddings, high retrieval precision, minimal context window bloat, but risks cross-sentence context fragmentation.
   - **800 Tokens (Large)**: Rich contextual completeness, multi-clause retention, but suffers from vector dilution and context noise.
   - **Overlap (50–100 tokens)**: Semantic glue preventing sentences and entities from being severed at chunk boundaries.
4. **Metadata Preservation**:
   - Retaining `source`, `page`, `chunk_id`, and `token_count` to enable verifiable enterprise LLM citations.

---

## 🏗️ Modular Architecture

```
day_03/session_2/
├── .env                       # API credentials & model configurations
├── requirements.txt           # Python dependencies
├── docs/                      # 3 Generated Multi-Page Domain PDFs
│   ├── cloud_platform_sla.pdf          (3 pages, ~2800 words)
│   ├── employee_travel_policy.pdf      (3 pages, ~2700 words)
│   └── database_migration_guide.pdf    (3 pages, ~2600 words)
├── generate_sample_docs.py    # ReportLab script generating multi-page PDFs
├── pdf_loader.py              # Page-by-page PDF ingestion & metadata extraction
├── chunker.py                 # Token-aware RecursiveCharacterTextSplitter (300 vs 800)
├── embedder.py                # Batched Gemini gemini-embedding-001 with disk caching
├── retriever.py               # NumPy Top-K cosine similarity search engine
├── evaluator.py               # 6-query benchmark suite & LLM answer synthesis
├── main.py                    # Master orchestration and comparative reporting
└── README.md                  # Comprehensive educational guide
```

---

## 🔬 Chunking Strategies: Comparative Analysis

| Strategy | Delimiters / Logic | Preservation of Meaning | Computational Cost | Ideal Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Fixed-Size Chunking** | Slices every $N$ characters strictly | ❌ Poor (cuts words and sentences in half) | ⚡ Extremely Low | Fixed-width log lines, binary dumps |
| **Recursive Character Chunking** | `["\n\n", "\n", ". ", " ", ""]` | ✅ High (prioritizes paragraphs, then sentences) | ⚡ Very Low | Standard unstructured text, enterprise documentation, contracts |
| **Semantic Chunking** | Cosine distance between sentence embeddings | ⭐ Maximum (breaks only on topic changes) | 🐢 High ($N$ embedding API calls per document) | Academic literature, essays without clear sub-headings |

---

## ⚖️ Chunk Size & Overlap Trade-Off Matrix

```
                          CHUNK SIZE SPECTRUM
   Small Chunks (100–300 Tokens)             Large Chunks (800–1500 Tokens)
   ◄──────────────────────────────────────────────────────────────────────►
   [+] High Retrieval Precision              [+] Full Context Retention
   [+] Minimal Context Window Bloat          [+] Keeps Multi-Step Rules Together
   [+] Lower LLM Prompt Cost                 [-] Vector Dilution (Averaged Topics)
   [-] Risk of Splitting Antecedents         [-] Wasted Context & Prompt Bloat
   [-] Missing Cross-Paragraph Nuance        [-] Potential Hallucination Distraction
```

### Why Overlap is Mandatory
If a crucial condition spans across two chunks (e.g. `"...unless authorized by VP"` starts at token 295 and ends at token 315), a chunker without overlap clips the sentence.
By configuring **50 tokens of overlap** on 300-token chunks, and **100 tokens of overlap** on 800-token chunks:
- The tail of Chunk $N$ is duplicated at the start of Chunk $N+1$.
- Any query matching either the condition or the rule finds the complete thought intact.

---

## 🚀 Quickstart & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```ini
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-3.5-flash-lite
EMBEDDING_MODEL=gemini-embedding-001
OPENAI_API_KEY=your_gemini_api_key
```

### 3. Run Pipeline
```bash
python main.py
```

---

## 📊 Benchmark Design (6 Enterprise Queries)

The evaluation suite tests 6 queries across all 3 PDFs requiring pinpoint numbers, multi-clause conditionals, and architectural thresholds:
1. **Q1 (Cloud SLA)**: Guaranteed Monthly Uptime for Tier 1 vs. 99.85% availability credit tier.
2. **Q2 (Cloud SLA)**: Database RTO/RPO commitments and DDoS exclusion thresholds.
3. **Q3 (Travel Policy)**: Business class restrictions, approval hierarchy, and first-class prohibition.
4. **Q4 (Travel Policy)**: Daily meal per diem breakdown and emergency medical SOS policy/hotline.
5. **Q5 (DB Migration)**: CDC engine, logical decoding plugin, and replication lag cutoff.
6. **Q6 (DB Migration)**: Planned cutover window, DNS TTL lead time, and automated rollback triggers.
