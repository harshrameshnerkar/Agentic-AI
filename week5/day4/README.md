# Day 4: Confidence Scoring & The Human Review Queue

> **Task 5: Document Extraction Pipeline**  
> **Track:** Generative AI  
> **Core Focus:** Architecting a calibrated 0.0 to 1.0 confidence score signal based on critical anchors, financial arithmetic coherence, and source fidelity; tuning the routing threshold with empirical ground truth data; and building a persistent Human-in-the-Loop review queue.

---

## 1. Executive Summary & Deliverables

No production LLM extraction pipeline is 100% accurate. The defining enterprise architecture question is: **What happens to the uncertain cases?** Silently passing uncertain or hallucinated extractions into downstream financial ERPs creates massive ledger reconciliation disasters.

On Day 4, we delivered:
1. **Multi-Factor Confidence Engine ([`confidence_engine.py`](../pipeline/confidence_engine.py)):**
   - Synthesizes 4 weighted factors into a composite 0.0 to 1.0 score:
     - **Critical Anchors (0.35):** Presence of `invoice_id`, `total_amount`, and `invoice_date`.
     - **Financial Arithmetic Coherence (0.30):** Validates that `subtotal + tax_amount == total_amount` (with freight/shipping tolerance).
     - **Source Fidelity (0.20):** Credits vector text PDFs with higher intrinsic confidence than degraded scans or mobile photos.
     - **Validation Stability (0.15):** Penalizes extractions that required multiple Pydantic schema retries.
2. **Empirical Threshold Tuner ([`tune_thresholds.py`](tune_thresholds.py)):**
   - Evaluated 8 candidate thresholds ($\theta \in [0.60, 0.95]$) across all 40 ground truth documents.
   - Selected **$\theta = 0.80$** as the optimal operating cutoff: achieves **85.0% Auto-Approval (Straight-Through Processing)** with **0.0% Escaped Financial Errors**.
3. **Threshold Analysis Report ([`CONFIDENCE_ROUTING_ANALYSIS.md`](CONFIDENCE_ROUTING_ANALYSIS.md)):**
   - Full trade-off matrix documenting Auto-Approval Rate vs. Escaped Error Rate vs. Human Review Load.
4. **Persistent Human Review Queue ([`review_queue.py`](review_queue.py)):**
   - Ingests low-confidence or arithmetic-mismatched extractions with explicit human-readable reasons (e.g. `['Severe arithmetic mismatch: 194.92 + 19.49 != 999.00']`).
   - Persists queue items and operator override actions to `data/review_queue.json`.

---

## 2. Verification & Execution

Run the Day 4 Acceptance Verification Suite:
```bash
python week5/day4/verify_day4.py
```

Run the Threshold Sweep Audit:
```bash
python week5/day4/tune_thresholds.py
```
