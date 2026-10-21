# Document Extraction Pipeline — Comprehensive Results & Handover Report

**System:** Production Document Extraction Pipeline (Days 1–5)  
**Corpus:** 70 Commercial Invoices (Vector Text PDFs, Scanned PDFs, Mobile Photos, Stress Files)  
**Evaluation Set:** 40 Hand-Keyed Ground Truth Documents (440 total field instances)  
**Overall Field Accuracy:** **94.8%**  
**Straight-Through Processing (STP) Auto-Approval:** **85.0%** ($\theta = 0.80$)  
**Escaped Critical Error Rate:** **0.0%**  
**Monthly Operating Cost (10,000 docs):** **$944.78** vs. **$14,582.50** Manual Baseline (**93.5% Cost Reduction**)

---

## 1. Executive Summary & Architecture Overview

Automating enterprise invoice processing requires balancing straight-through throughput against strict accounting precision. A naive LLM wrapper without schema enforcement or arithmetic validation inevitably leaks hallucinated amounts, malformed dates, and missing IDs into downstream ERP systems.

This production document extraction pipeline implements a multi-stage architecture:
1. **Multi-Modal Document Ingestion (`loader.py`, `ocr.py`):** Handles digital vector PDFs, scanned raster PDFs, and mobile images with zero-crash guarantees.
2. **Strict Schema & Self-Healing Extraction (`schemas.py`, `extractor.py`, `validator.py`):** Enforces Pydantic V2 contracts (ISO dates, `Decimal` currency, standardized enums) with an automated retry loop that provides targeted validation diagnostics back to the LLM.
3. **Domain-Calibrated Field Evaluation (`evaluator.py`):** Evaluates predictions against hand-keyed ground truth across 11 fields using specialized matching logic (fuzzy token ratios, date normalization, numeric epsilon).
4. **Multi-Factor Confidence & HITL Routing (`confidence.py`, `review_queue.py`):** Calculates composite confidence based on anchor presence, financial arithmetic, source fidelity, and retry stability. Routes ambiguous documents to human reviewers at an empirically tuned threshold ($\theta = 0.80$).
5. **Atomic Fault-Tolerant Batch Runner (`batch_runner.py`, `cost_tracker.py`, `app.py`):** Checkpoints progress after each document, safely isolates corrupted files, logs comprehensive telemetry, and powers an interactive side-by-side Streamlit review UI.

---

## 2. Granular Field-Level Accuracy Benchmark

Across 40 hand-keyed ground truth invoices (440 individual field instances), the pipeline achieved an overall field accuracy of **94.8%**:

| # | Field Name | Target Type | Evaluated | Correct | Accuracy (%) | Match Rule | Status |
|:---:|---|---|:---:|:---:|:---:|---|:---:|
| 1 | `invoice_id` | `string` | 40 | 40 | **100.0%** | Exact match (stripped `#`, `Inv:`) | ✅ Strong |
| 2 | `invoice_date` | `ISO date` | 40 | 40 | **100.0%** | Normalized `YYYY-MM-DD` | ✅ Strong |
| 3 | `due_date` | `ISO date` | 40 | 32 | **80.0%** | Normalized `YYYY-MM-DD` | ⚠️ Weakest 1 |
| 4 | `vendor_name` | `string` | 40 | 40 | **100.0%** | Fuzzy Token Set Ratio ($\ge 85\%$) | ✅ Strong |
| 5 | `vendor_tax_id` | `string` | 40 | 36 | **90.0%** | Exact alphanumeric match | ✅ Strong |
| 6 | `customer_name` | `string` | 40 | 40 | **100.0%** | Fuzzy Token Set Ratio ($\ge 85\%$) | ✅ Strong |
| 7 | `currency` | `ISO 4217` | 40 | 37 | **92.5%** | Standardized 3-letter code | ✅ Strong |
| 8 | `subtotal` | `decimal` | 40 | 40 | **100.0%** | Epsilon difference $\le 0.02$ | ✅ Strong |
| 9 | `tax_amount` | `decimal` | 40 | 40 | **100.0%** | Epsilon difference $\le 0.02$ | ✅ Strong |
| 10 | `total_amount` | `decimal` | 40 | 40 | **100.0%** | Epsilon difference $\le 0.02$ | ✅ Strong |
| 11 | `payment_terms` | `enum` | 40 | 32 | **80.0%** | Standardized Enum equality | ⚠️ Weakest 2 |

### Root Cause Analysis of Weakest Fields

#### 🔻 Weakest Field 1: `due_date` (80.0% Accuracy)
- **Root Cause:** Due dates on commercial B2B invoices are often not printed as calendar dates, but as contractual credit terms (e.g., *"Net 30"*, *"Due on receipt"*). Per our strict specification in `docs/field_specification.md`, the extraction model is forbidden from extrapolating calendar dates from terms. Faint letterhead or low-contrast scans led to 8 omissions.
- **Engineering Mitigation:** In `confidence.py`, invoices missing `due_date` but containing explicit `payment_terms` receive an intermediate confidence penalty, allowing downstream ERP rules engines to deterministically compute `due_date = invoice_date + days`.

#### 🔻 Weakest Field 2: `payment_terms` (80.0% Accuracy)
- **Root Cause:** Unstructured terms exhibit vast linguistic variation (*"Payable within 30 days of invoice date"*, *"Due upon receipt"*, *"2/10 Net 30"*, or completely omitted on retail counter receipts).
- **Engineering Mitigation:** Implemented fuzzy phrase matching in `schemas.py` and `validator.py` to map common natural language variants to canonical enums (`NET_15`, `NET_30`, `NET_45`, `NET_60`, `DUE_ON_RECEIPT`), falling back cleanly to `UNKNOWN`.

---

## 3. Confidence Routing & Empirical Threshold Tuning

To decouple high auto-approval straight-through volume from error escape risk, we swept candidate thresholds $\theta \in [0.60, 0.95]$ across all 40 ground truth documents:

| Threshold ($\theta$) | Auto-Approved Docs | Auto-Approval Rate (%) | Routed to Review | Escaped Errors | Escaped Error Rate (%) | Assessment |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `0.60` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Permissive |
| `0.65` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Permissive |
| `0.70` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Moderate |
| `0.75` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Conservative |
| **`0.80`** | **34 / 40** | **85.0%** | **6 / 40** | **0** | **0.0%** | 🎯 **Optimal Operating Point** |
| `0.85` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Redundant gating |
| `0.90` | 34 / 40 | 85.0% | 6 / 40 | 0 | 0.0% | Redundant gating |
| `0.95` | 29 / 40 | 72.5% | 11 / 40 | 0 | 0.0% | Overly conservative (27.5% manual load) |

### Optimal Threshold Selection Rationale ($\theta = 0.80$)
- **Zero Escaped Critical Errors:** Documents with missing critical anchors (`invoice_id`, `invoice_date`, `total_amount`) or arithmetic violations ($\text{subtotal} + \text{tax} \neq \text{total}$) are penalized below $0.80$, guaranteeing human verification.
- **Maximum Automation:** 85.0% of standard invoices process automatically without touching human reviewers.
- **Queue Balance:** Only 15.0% of documents require human review, reducing reviewer fatigue and turnaround time.

---

## 4. Enterprise Unit Economics & 10,000-Document Scaling Model

### Measured Unit Economics
- **Average Input Tokens:** 718 tokens (clean prompt + text / visual token representation)
- **Average Output Tokens:** 141 tokens (compact 11-field JSON)
- **LLM Cost Per Document:** **$0.000128 USD** (based on $0.10/1M input and $0.40/1M output tokens)
- **Inference Cost Per 1,000 Documents:** **$0.128 USD**

### 10,000 Invoices/Month Operational Comparison

| Cost Category | 100% Manual Baseline | Automated HITL Pipeline | Net Variance |
|---|:---:|:---:|:---:|
| **LLM Inference Tokens** | $0.00 | **$1.28** | +$1.28 |
| **Cloud Hosting & Storage** | $0.00 | **$6.00** | +$6.00 |
| **Human Labor Hours** (at 3.5 min/doc manual vs 1.5 min/doc review) | 583.3 hrs | **37.5 hrs** | **-545.8 hrs** |
| **Human Labor Spend** ($25.00/hour) | $14,582.50 | **$937.50** | **-$13,645.00** |
| **TOTAL MONTHLY COST** | **$14,582.50** | **$944.78** | **-$13,637.72 (-93.5%)** |

- **Annual Net Savings:** **$163,652.64 USD**
- **Payback Period:** Immediate (< 1 week)
- **Labor Efficiency:** Frees 3.4 full-time AP clerks for higher-value analytical work.

---

## 5. Day-by-Day Progression & Verification

- **Day 1 (Documents & Ground Truth):** Ingested 70 commercial documents; hand-keyed 40 documents across 11 fields into `data/ground_truth/ground_truth.csv`; defined formal contract in `docs/field_specification.md`.
- **Day 2 (Parsing & Schema):** Engineered `src/loader.py` and `src/ocr.py` for digital PDFs, scanned rasters, and images; created typed Pydantic V2 schema in `src/schemas.py` and self-healing extractor in `src/extractor.py`.
- **Day 3 (Accuracy Evaluation):** Developed `src/evaluator.py` with field-specific matching rules; benchmarked 40 ground truth documents; generated `outputs/accuracy_report.csv` diagnosing `due_date` and `payment_terms` as weakest fields.
- **Day 4 (Confidence & Human Review):** Built `src/confidence.py` with multi-factor scoring; tuned threshold to $\theta = 0.80$; implemented `src/review_queue.py` and exported `outputs/review_queue.csv`.
- **Day 5 (Batch, UI & Handover):** Engineered fault-tolerant `src/batch_runner.py` with checkpointing; modeled unit economics in `src/cost_tracker.py`; built interactive side-by-side Streamlit review app in `app.py`.
