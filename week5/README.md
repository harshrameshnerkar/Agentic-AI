# TASK 5: Document Extraction Pipeline

| Track | Estimated Effort | Core Competencies | Status |
|-------|------------------|-------------------|--------|
| **Gen AI** | 5 Days (37.5 hrs) | Structured Output, Field-Level Accuracy, Human-in-the-Loop Routing, Batch Reliability | **Day 1 Complete** (20%) |

---

## 5-Day Roadmap & Deliverables

| Day | Focus | Deliverable | Status |
|:---:|:------|:------------|:------:|
| **Day 1** | **Documents, Field Spec & Ground Truth** | Written field specification, 70 real documents, 40-doc ground truth committed before extraction code | **COMPLETED** |
| **Day 2** | Parsing & The Extraction Schema | Multi-modal loader (text PDFs, scanned PDFs, images) + typed Pydantic schema with retries | Planned |
| **Day 3** | Field-Level Accuracy | Scorer per field across 40 ground truth docs, identify two weakest fields | Planned |
| **Day 4** | Confidence & Human Review Queue | Confidence routing threshold, review queue, auto-approval rate & error rate tuning | Planned |
| **Day 5** | Batch Pipeline, Cost & Handover | Batch processing pipeline, corrupt document survival, Streamlit side-by-side UI, cost projection | Planned |

---

## Acceptance Criteria Checklist

| # | Criterion | Verification Method | Status |
|:-:|:----------|:-------------------|:------:|
| 1 | A written field specification exists with a rule for every field, including missing values | Mentor picks 3 fields and asks what happens when each is absent | **MET (Y)** |
| 2 | Ground truth hand-keyed for 40 documents, committed before extraction code | Check git log - ground truth file predates extraction code | **MET (Y)** |
| 3 | Loader handles text PDFs, scanned PDFs and images without crashing | Drop a scanned document into folder and run | *Day 2* |
| 4 | Output is enforced by a typed schema - dates, decimals and enums, not loose strings | Read schema and try to make it accept a malformed date | *Day 2* |
| 5 | Accuracy is reported per field, not only per document | Open accuracy table and check weakest field | *Day 3* |
| 6 | Matching rules are sensible per field type and documented | Verify normalization before scoring | *Day 3* |
| 7 | Confidence signal exists and routes low-confidence extractions to review | Feed poor-quality scan and confirm flagged | *Day 4* |
| 8 | Review threshold is tuned with evidence, not picked arbitrarily | Verify auto-approval rate and error rate | *Day 4* |
| 9 | Batch pipeline survives a bad document mid-run without losing prior work | Run with corrupt file in middle | *Day 5* |
| 10| Cost per document measured and projected to 10,000 documents | Cost calculation table provided | *Day 5* |
| 11| README allows second person to run pipeline from clean clone | Mentor clones and runs without questions | *Day 5* |

---

## Project Structure

```text
week5/
├── README.md                   # Overall project roadmap and acceptance tracker
├── FIELD_SPECIFICATION.md      # Official 11-field extraction contract & missing value policies
├── data/
│   ├── ground_truth_40.json    # 40 hand-keyed, verified ground truth records (JSON)
│   ├── ground_truth_40.csv     # 40 hand-keyed, verified ground truth records (CSV)
│   └── documents/              # 70 real documents (25 text PDFs, 10 scanned PDFs, 5 images, 30 holdouts)
└── day1/
    ├── README.md               # Day 1 technical documentation & Mentor QA
    ├── prepare_real_dataset.py # Real dataset ingestion, conversion & ground truth compiler
    └── verify_day1.py          # Day 1 acceptance criteria verification test suite
```
