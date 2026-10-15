# TASK 5: Production Document Extraction Pipeline

| Track | Estimated Effort | Core Competencies | Status |
|-------|------------------|-------------------|:------:|
| **Gen AI** | 5 Days (37.5 hrs) | Structured Output, Field-Level Accuracy, Human-in-the-Loop Routing, Batch Reliability, Streamlit UI | **100% COMPLETE (Days 1–5)** |

---

## 5-Day Roadmap & Deliverables

| Day | Focus | Deliverable | Status |
|:---:|:------|:------------|:------:|
| **Day 1** | **Documents, Field Spec & Ground Truth** | Written field specification, 70 real documents, 40-doc ground truth committed before extraction code | **COMPLETED** |
| **Day 2** | **Parsing & The Extraction Schema** | Multi-modal loader (text PDFs, scanned PDFs, images) + typed Pydantic V2 schema with validation retries | **COMPLETED** |
| **Day 3** | **Field-Level Accuracy** | Scorer per field across 40 ground truth docs (94.8% field accuracy), identified two weakest fields (`due_date`, `payment_terms`) | **COMPLETED** |
| **Day 4** | **Confidence & Human Review Queue** | Multi-factor confidence score, empirical threshold tuning ($\theta = 0.80 \rightarrow$ 85% auto-approval, 0.0% escaped critical errors), persistent review queue | **COMPLETED** |
| **Day 5** | **Batch Pipeline, Cost & Handover** | Crash-proof batch pipeline surviving corrupt files, 10,000-doc cost model ($13.6k/mo savings, -93.5%), interactive Streamlit review UI | **COMPLETED** |

---

## Acceptance Criteria Checklist (11/11 Verified)

| # | Criterion | Verification Method | Status |
|:-:|:----------|:-------------------|:------:|
| 1 | A written field specification exists with a rule for every field, including missing values | Mentor picks 3 fields and asks what happens when each is absent (`FIELD_SPECIFICATION.md`) | **MET (Y)** |
| 2 | Ground truth hand-keyed for 40 documents, committed before extraction code | Check git log - ground truth file predates extraction code | **MET (Y)** |
| 3 | Loader handles text PDFs, scanned PDFs and images without crashing | Drop a scanned document or corrupted file into folder and run (`verify_day2.py`) | **MET (Y)** |
| 4 | Output is enforced by a typed schema - dates, decimals and enums, not loose strings | Read schema and try to make it accept a malformed date (`verify_day2.py`) | **MET (Y)** |
| 5 | Accuracy is reported per field, not only per document | Open accuracy table and check weakest field (`ACCURACY_REPORT.md`, `verify_day3.py`) | **MET (Y)** |
| 6 | Matching rules are sensible per field type and documented | Verify normalization before scoring (`field_matcher.py`, `verify_day3.py`) | **MET (Y)** |
| 7 | Confidence signal exists and routes low-confidence extractions to review | Feed poor-quality scan and confirm flagged to queue (`verify_day4.py`) | **MET (Y)** |
| 8 | Review threshold is tuned with evidence, not picked arbitrarily | Verify auto-approval rate and error rate tradeoff curve (`CONFIDENCE_ROUTING_ANALYSIS.md`) | **MET (Y)** |
| 9 | Batch pipeline survives a bad document mid-run without losing prior work | Run with corrupt file (`doc_069_corrupt.pdf`) in middle (`verify_day5.py`) | **MET (Y)** |
| 10| Cost per document measured and projected to 10,000 documents | Cost calculation table provided (`COST_AND_SCALING_REPORT.md`) | **MET (Y)** |
| 11| README allows second person to run pipeline from clean clone | Mentor clones and runs without questions + interactive Streamlit UI | **MET (Y)** |

---

## Project Structure

```text
week5/
├── README.md                   # Overall project roadmap and master acceptance tracker
├── FIELD_SPECIFICATION.md      # Official 11-field extraction contract & missing value policies
├── verify_week5_all.py         # Master test runner validating all 11 Acceptance Criteria
├── data/
│   ├── ground_truth_40.json    # 40 hand-keyed, verified ground truth records (JSON)
│   ├── ground_truth_40.csv     # 40 hand-keyed, verified ground truth records (CSV)
│   ├── extractions_cache.json  # Cached deterministic extractions for reproducibility
│   ├── review_queue.json       # Persistent Human-in-the-Loop review queue
│   ├── documents/              # 70 real documents (25 text PDFs, 10 scanned PDFs, 5 images, 30 holdouts)
│   └── batch_output/           # Output directory for production batch runs
├── pipeline/                   # Production Extraction Engine Modules
│   ├── document_loader.py      # Multimodal loader (text PDFs, scanned PDFs, images, corrupt/blank)
│   ├── extraction_schema.py    # Strict Pydantic V2 schema (date, Decimal, Enum)
│   ├── extractor.py            # Multimodal vision LLM caller + Pydantic validation retry loop
│   ├── field_matcher.py        # Domain-specific field matcher (fuzzy strings, decimal epsilon)
│   ├── confidence_engine.py    # Multi-factor confidence scoring & human review router
│   └── batch_runner.py         # Fault-tolerant batch runner with atomic checkpointing
├── day1/                       # Day 1: Real Documents, Field Spec & Ground Truth
│   ├── README.md               # Technical documentation
│   ├── prepare_real_dataset.py # Real dataset ingestion & ground truth compiler
│   └── verify_day1.py          # Day 1 acceptance test suite
├── day2/                       # Day 2: Parsing & The Extraction Schema
│   ├── README.md               # Technical documentation
│   ├── inspect_ocr_errors.py   # OCR failure-mode catalog & schema defenses
│   └── verify_day2.py          # Day 2 acceptance test suite
├── day3/                       # Day 3: Field-Level Accuracy
│   ├── README.md               # Technical documentation
│   ├── field_evaluator.py      # Field-by-field accuracy calculator
│   ├── ACCURACY_REPORT.md      # Granular 11-field accuracy report & weakest fields analysis
│   └── verify_day3.py          # Day 3 acceptance test suite
├── day4/                       # Day 4: Confidence & Human Review Queue
│   ├── README.md               # Technical documentation
│   ├── tune_thresholds.py      # Empirical routing threshold tuner
│   ├── review_queue.py         # Human-in-the-Loop queue manager
│   ├── CONFIDENCE_ROUTING_ANALYSIS.md # Auto-approval vs error rate trade-off report
│   └── verify_day4.py          # Day 4 acceptance test suite
└── day5/                       # Day 5: Batch Pipeline, Cost & Handover
    ├── README.md               # Technical documentation
    ├── batch_pipeline.py       # Production batch CLI runner
    ├── cost_calculator.py      # Unit economics & 10,000-doc financial scaling model
    ├── streamlit_app.py        # Interactive side-by-side review UI
    ├── COST_AND_SCALING_REPORT.md # 1-page financial scaling report
    └── verify_day5.py          # Day 5 acceptance test suite
```

---

## Quickstart & Verification Commands

You can run commands either from the repository root (`Agentic-AI/`) or directly from inside the `week5/` folder:

### 1. Run Complete Master Verification Suite (All 11 Acceptance Criteria):
```bash
# If inside week5/ directory:
python verify_week5_all.py

# If in repository root:
python week5/verify_week5_all.py
```

### 2. Launch Interactive Streamlit Review UI:
```bash
# If inside week5/ directory:
streamlit run app.py
# (or: streamlit run day5/streamlit_app.py)

# If in repository root:
streamlit run week5/app.py
# (or: streamlit run week5/day5/streamlit_app.py)
```
Open **`http://localhost:8501`** in your browser.

### 3. Run Production Batch Pipeline on All Documents:
```bash
# If inside week5/ directory:
python day5/batch_pipeline.py --input-dir data/documents/ --output-dir data/batch_output/

# If in repository root:
python week5/day5/batch_pipeline.py --input-dir week5/data/documents/ --output-dir week5/data/batch_output/
```

### 4. Run Daily Suites Individually:
```bash
python week5/day1/verify_day1.py  # Criteria 1 & 2
python week5/day2/verify_day2.py  # Criteria 3 & 4
python week5/day3/verify_day3.py  # Criteria 5 & 6
python week5/day4/verify_day4.py  # Criteria 7 & 8
python week5/day5/verify_day5.py  # Criteria 9, 10 & 11
```
