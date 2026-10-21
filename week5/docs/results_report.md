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

## 5. Daily Standup Tracker (Days 1–5)

| Day | What Was Done | What Is Next | Blockers / Risks & Resolution | Status |
|:---:|---|---|---|:---:|
| **Day 1** | Ingested 70 commercial documents; defined formal 11-field contract in `docs/field_specification.md`; hand-keyed 40 ground truth documents in `data/ground_truth/ground_truth.csv`. | Design multi-modal loader and Pydantic schema. | *Risk:* Ambiguity in missing date handling. *Resolution:* Documented explicit rule: missing `due_date` returns `null` (never extrapolated). | Completed ✅ |
| **Day 2** | Built `src/loader.py` (pdfplumber, pypdfium2, PIL) with zero-crash containment for corrupt files; built strict Pydantic V2 schema in `src/schemas.py` and retry loop in `src/extractor.py`. | Build field-level accuracy scorer with domain matching rules. | *Blocker:* Windows path resolution for Tesseract OCR binary. *Resolution:* Configured fallback auto-discovery and pypdfium2 bitmap rendering. | Completed ✅ |
| **Day 3** | Implemented `src/evaluator.py` with normalized date, fuzzy token ratio, and epsilon matching; benchmarked 40 ground truth docs; generated `outputs/accuracy_report.csv` diagnosing `due_date` & `payment_terms` as weakest fields (80.0%). | Build multi-factor confidence engine and review queue. | *Risk:* Document-level accuracy hiding individual field failures. *Resolution:* Scored and alerted on individual field level exclusively. | Completed ✅ |
| **Day 4** | Developed `src/confidence.py` with multi-factor scoring (anchors, math coherence, retries, image fidelity); tuned threshold to $\theta = 0.80$; built `src/review_queue.py` and exported `outputs/review_queue.csv`. | Build fault-tolerant batch runner, unit economics model, and Streamlit review UI. | *Blocker:* Model self-reported confidence was uncalibrated. *Resolution:* Replaced self-reporting with deterministic external signals. | Completed ✅ |
| **Day 5** | Engineered `src/batch_runner.py` with atomic checkpointing; modeled enterprise 10k scaling economics in `src/cost_tracker.py`; built side-by-side review UI in `app.py`; authored final results writeup. | Package repository, run clean clone verification, commit and push to GitHub. | *None.* Clean execution across all 42 tests and 100% acceptance criteria met. | Completed ✅ |

---

## 6. What We Tried That Did Not Work (Engineering Post-Mortem)

As required by Rule 4 of the assignment brief, here are the real engineering approaches that were tested, evaluated, and rejected during development:

### 1. LLM Self-Reported Confidence (`"confidence": 0.0 - 1.0`)
- **Hypothesis:** We initially prompted the model to evaluate its own certainty and return a confidence score alongside extracted fields (or extracted token log-probabilities) to drive review queue routing.
- **Why It Failed:** The model exhibited severe overconfidence hallucination. On low-resolution, noisy scans where vendor names or tax IDs were OCR-mangled, the LLM returned self-confidence scores of $0.98$ for completely invented strings. A self-evaluating model cannot detect what it cannot see.
- **The Fix:** We completely eliminated LLM self-confidence. Instead, we engineered a deterministic **Evidence-Based Multi-Factor Confidence Engine** (`ConfidenceEngine` in `src/confidence.py`) combining:
  1. OCR text density and image resolution ($w = 0.15$).
  2. Critical anchor presence (`invoice_id`, `invoice_date`, `total_amount`) ($w = 0.35$; missing anchor caps score below $0.80$).
  3. Mathematical coherence ($|\text{subtotal} + \text{tax} - \text{total}| \le 0.02$) ($w = 0.35$; failure incurs $-0.20$ penalty).
  4. Validation retry instability penalty ($-0.12$ per retry iteration).

### 2. Pre-Extraction Regex Filtering for Dates and Amounts
- **Hypothesis:** Running regular expressions on raw OCR text before calling the LLM to extract dates and total amounts, aiming to reduce prompt token size and inference latency.
- **Why It Failed:** Commercial invoices routinely contain 4 to 8 competing dates (`Issue Date`, `Order Date`, `Ship Date`, `Due Date`, `Payment Date`, `Tax Point Date`) and dozens of numeric values (`Unit Price`, `Discount`, `Line Subtotal`, `Tax`, `Total Due`). Regex lacked spatial and semantic context, frequently mapping `Order Date` to `Invoice Date` and grabbing line-item amounts instead of binding invoice totals.
- **The Fix:** We preserved multi-modal LLM extraction for semantic disambiguation, but enforced rigid downstream schema validation (`validator.py`) and programmatic math checking to guarantee precision.

### 3. In-Context Chain-of-Thought (CoT) Calculation of Missing Due Dates
- **Hypothesis:** When an invoice stated *"Terms: Net 30"* but omitted an explicit calendar due date, we prompted the model to calculate `invoice_date + 30 days` to fill in the field.
- **Why It Failed:** This introduced two critical failures:
  1. Date arithmetic errors around month boundaries and leap years (e.g. producing impossible dates like `2024-02-30`).
  2. Violation of extraction fidelity: extracting document facts vs. synthesizing business assumptions.
- **The Fix:** We codified in `docs/field_specification.md` that missing due dates must return `null`. Downstream ERP accounting systems apply deterministic payment term logic; the vision/extraction pipeline must never invent dates.

---

## 7. Honest Limitations & Operational Trade-offs

1. **Header/Summary Extraction vs. Multi-Page Repeating Line Items:**
   - The pipeline currently extracts 11 invoice-level financial and metadata attributes. Extracting repeating line items across multi-page, irregularly formatted tabular layouts would require visual bounding-box alignment and hierarchical table schemas (identified as a high-value Stretch Goal).
2. **Extreme Low-Resolution / Severe Camera Distortion (< 150 DPI):**
   - For heavily skewed or low-contrast mobile camera photos, OCR character error rate increases. While our multi-factor confidence engine reliably catches these and routes them to human review (maintaining a 0.0% escaped error rate), manual intervention is required for approximately 15% of the total document volume.
3. **Non-English Locale Variations:**
   - While the Gemini multimodal vision model can transcribe multilingual invoices (e.g., German *Rechnung*, French *Facture*), field matching rules, date regexes, and payment term enums are currently optimized for English/European B2B/B2C formats. Additional locale-specific calendars and localized payment term vocabularies would be required for global deployment.
