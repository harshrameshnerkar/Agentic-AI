# Task 5: Document Extraction Pipeline — 1-Page Results & Handover Write-Up

**Engineer:** Learner / GenAI Systems Specialist  
**System:** OpsExtract AI (Production Document Extraction & HITL Verification)  
**Status:** 100% Complete across all 5 Days (11/11 Acceptance Criteria Passed)  

---

## 1. Executive Summary & Architecture Overview

Automating enterprise financial documents (invoices, purchase orders, bills) requires balancing high straight-through processing (STP) volume against strict financial precision. A generic LLM extraction without validation risks hallucinated figures, malformed dates, and undetected errors slipping into ERP systems.

Over this 5-day build, we engineered a production-grade, multi-modal invoice extraction pipeline that:
1. **Enforces Strict Typed Contracts:** Uses Pydantic V2 to enforce real dates (`datetime.date`), exact monetary decimals (`decimal.Decimal`), and standardized enums, backed by an automated self-healing validation retry loop.
2. **Evaluates Granular Field Accuracy:** Evaluates per-field performance across 40 hand-keyed ground truth documents using domain-specific matching rules (fuzzy token matching, decimal epsilons, date normalization).
3. **Calibrates Human-in-the-Loop Routing:** Dynamically scores multi-factor confidence and routes uncertain cases to a persistent review queue, keeping accounting ledgers clean.
4. **Delivers High Unit Economics:** Achieves an 85.0% auto-approval rate with zero escaped errors, cutting monthly processing costs by 93.5% ($13,638/mo saved at 10,000 documents).

---

## 2. Key Metrics & Empirical Findings

| Evaluation Dimension | Benchmark Result | Operational Impact |
|---|:---:|---|
| **Document Corpus** | **70 Real Invoices** | 50 text PDFs, 15 scanned raster PDFs, 5 mobile photos, 2 stress files |
| **Ground Truth Dataset** | **40 Hand-Keyed Docs** | Committed to git prior to extraction code (440 evaluated field instances) |
| **Overall Field Accuracy** | **94.8%** | 8 of 11 fields achieved $\ge 92.5\%$ accuracy; 6 fields scored a perfect 100% |
| **Weakest Fields Identified** | `due_date` (80.0%), `payment_terms` (80.0%) | Root causes: dynamic terms vs explicit calendar dates & freeform phrasing |
| **Optimal Routing Threshold** | **$\theta = 0.80$** | Swept across 0.60–0.95; 0.80 provides sweet spot between load and safety |
| **Straight-Through Processing** | **85.0% Auto-Approved** | 34 / 40 ground truth docs pass cleanly without requiring human intervention |
| **Escaped Critical Error Rate** | **0.0%** | Zero arithmetic mismatches or missing anchors escaped to auto-approval |
| **Measured Unit Cost** | **$0.000131 / doc** | Average: 748 input tokens, 141 output tokens ($0.131 per 1,000 documents) |
| **10k Monthly Projection** | **$944.81 total spend** | Down from $14,582.50 manual baseline (**-$13,637.69 / month net savings**) |

---

## 3. What Was Built (Day-by-Day Journey)

- **Day 1 (Field Spec & Ground Truth):** Defined the official 11-field extraction contract in `FIELD_SPECIFICATION.md` specifying what counts, missing value policies (strict `null` / `UNKNOWN`, no hallucinated dates), and output formats. Hand-keyed 40 real invoices into `ground_truth_40.json` before writing extraction code.
- **Day 2 (Parsing & Typed Schema):** Built `DocumentLoader` using `pdfplumber`, `pypdfium2`, and `PIL` to handle text PDFs, scanned PDFs, and raster photos with zero unhandled crashes. Designed `InvoiceExtraction` in `extraction_schema.py` and wrapped it in `extractor.py` with an automated retry loop that catches `ValidationError` and feeds error feedback back to the model.
- **Day 3 (Field-Level Accuracy):** Implemented `FieldMatcher` and `FieldEvaluator` to measure accuracy per field instead of per document. Applied fuzzy matching ($\ge 85\%$) for vendor/customer names, decimal epsilon ($\le 0.02$) for currency, and normalized dates. Generated `ACCURACY_REPORT.md` diagnosing `due_date` and `payment_terms` as the weakest fields.
- **Day 4 (Confidence & Review Queue):** Built `ConfidenceEngine` scoring critical anchor presence, arithmetic consistency (`subtotal + tax == total`), image fidelity, and retry stability. Swept candidate thresholds (0.60 to 0.95) in `tune_thresholds.py` to prove $\theta=0.80$ optimizes straight-through volume while blocking errors. Persisted review items to `review_queue.json`.
- **Day 5 (Batch Pipeline, Cost & Review UI):** Created `BatchPipelineRunner` with atomic state checkpointing to process directories of documents surviving corrupted files (`doc_069_corrupt.pdf`). Built the interactive `streamlit_app.py` featuring side-by-side invoice rendering, field editor, batch telemetry, and interactive ROI modeling. Modeled 10,000-document economics in `COST_AND_SCALING_REPORT.md`.

---

## 4. Handover & Execution Instructions

```bash
# 1. Run Complete Master Verification Gate (Validates all 11 Acceptance Criteria):
python week5/verify_week5_all.py

# 2. Run Full Production Batch Pipeline on all 70 documents:
python week5/day5/batch_pipeline.py --input-dir week5/data/documents/ --output-dir week5/data/batch_output/

# 3. Launch Interactive Side-by-Side Review UI:
streamlit run week5/app.py
```
