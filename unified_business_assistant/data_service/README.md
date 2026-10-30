# Role B: Data Service — Unified Business Assistant

Structured Data, Text-to-SQL Generation, Pre-Execution Safety Validation, Self-Correction & Read-Only Execution.

---

## 1. Service Mission & Architecture
The **Data Service (Role B)** owns the enterprise database, schema context representation, text-to-SQL generation, strict AST-based safety validation, bounded read-only execution, and query self-correction. It serves the canonical `POST /query` endpoint (Interface 2) consumed by **Role C (Orchestrator)**.

```mermaid
flowchart TD
    UserQ[Role C POST /query] --> SchemaContext[1. Token-Efficient Schema Context Builder]
    SchemaContext --> Gen[2. Multi-Provider Text-to-SQL Generator]
    Gen --> SafetyGate{3. AST Safety Gate (sqlglot)}
    
    SafetyGate -- Destructive Operation Detected --> Block[Block at Validation Prior to DB Execution]
    SafetyGate -- Valid SELECT Query --> ReadOnlyConn[4. Read-Only DB Connection (mode=ro)]
    
    ReadOnlyConn -- Execution Error --> SelfCorrect[5. Self-Correction Loop (Max 3 Attempts)]
    SelfCorrect --> ReValidate{Re-Validate Corrected Query}
    ReValidate -- Safe --> ReadOnlyConn
    
    ReadOnlyConn -- Execution Success --> Formatter[6. Format Response: Columns + Rows + SQL]
    Formatter --> Response[QueryResponse to Role C]
    Block --> Response
```

---

## 2. Individual Acceptance Criteria Status

| #     | Acceptance Criterion | Verification Method | Status |
|-------|----------------------|---------------------|--------|
| **1** | Mock endpoint published on Day 1 morning | `mock_query_service.py` on port 8002 returns 2 hardcoded rows + fake SQL | **MET** |
| **2** | Real `/query` matches contract exactly | Role C consumes with zero schema drift (`contracts.py`) | **MET** |
| **3** | Destructive SQL blocked at validation before execution | Tested in `tests/test_safety.py`: `DROP TABLE` blocked prior to execution | **MET** |
| **4** | Service self-corrects failed queries using DB error feedback | Tested in `tests/test_self_correction.py`: 3 deliberately broken queries self-correct | **MET** |
| **5** | Written failure taxonomy with counts exists | Documented in `docs/FAILURE_TAXONOMY.md` with largest category resolved | **MET** |
| **6** | `answerable=false` for out-of-scope/unanswerable questions | Dual-gate semantic filtering in `sql/schema_context.py` and `tests/test_answerable.py` | **MET** |

---

## 3. Directory Layout
```text
data_service/
├── contracts.py              # Canonical Pydantic contract (QueryRequest, QueryResponse)
├── mock_query_service.py     # Day 1 mock service for Role C development (Port 8002)
├── app.py                    # Production FastAPI application (Port 8002)
├── db/
│   ├── enterprise_business.db# Authentic Northwind SQLite database (12 tables, 625,890 real rows)
│   ├── schema.sql            # DDL schema definition
│   ├── seed_database.py      # Upstream dataset downloader & validator
│   └── connection.py         # Read-only connection manager (mode=ro, query_only=ON)
├── safety/
│   ├── validator.py          # AST-based SQL parser & safety validator (sqlglot)
│   └── errors.py             # Structured safety exceptions
├── sql/
│   ├── schema_context.py     # Compact schema prompt builder & domain filter
│   ├── prompt_templates.py   # Prompts, rules, few-shot examples
│   └── generator.py          # Text-to-SQL engine (Groq, Gemini, OpenAI, Heuristic)
├── correction/
│   └── self_correction.py    # Self-correction engine with sanitized error feedback
├── evaluation/
│   ├── test_queries.json     # 40-question benchmark dataset
│   ├── failure_taxonomy.py   # Failure taxonomy categories & classifier
│   ├── run_evaluation.py     # Benchmark evaluator (100% accuracy on full suite)
│   └── EVAL_REPORT.json      # Structured benchmark results
├── tests/
│   ├── test_contract.py      # Contract compliance & parity tests
│   ├── test_database.py      # Row counts (>1000 rows) & foreign key integrity
│   ├── test_safety.py        # Destructive SQL validation tests
│   ├── test_self_correction.py# Deliberately broken query repair tests
│   └── test_answerable.py    # Answerable=False tests for unsupported queries
├── docs/
│   ├── SCHEMA.md             # ERD diagram, tables, and column documentation
│   ├── SAFETY_GUARANTEES.md  # Multi-layer safety architecture documentation
│   ├── FAILURE_TAXONOMY.md   # Taxonomy breakdown and mitigation report
│   └── REPOINTING_GUIDE.md   # Guide on pointing to other SQLite or PostgreSQL DBs
└── requirements.txt          # Python dependencies
```

---

## 4. Quickstart & Commands

### 4.1 Running the Day 1 Mock Service
```bash
uvicorn mock_query_service:app --host 127.0.0.1 --port 8002 --reload
```

### 4.2 Running the Production Service
```bash
uvicorn app:app --host 127.0.0.1 --port 8002 --reload
```

### 4.3 Testing the Health Endpoint
```bash
curl http://127.0.0.1:8002/health
```
 
### 4.4 Running Automated Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 4.5 Running the 40-Question Benchmark
```bash
python evaluation/run_evaluation.py
```
