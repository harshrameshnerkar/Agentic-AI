# Day 3: Field-Level Accuracy & Granular Benchmarking

> **Task 5: Document Extraction Pipeline**  
> **Track:** Generative AI  
> **Core Focus:** Evaluating extraction accuracy across all 40 hand-keyed ground truth documents field-by-field, enforcing canonical matching rules (fuzzy strings, normalized ISO dates, decimal epsilons, enum equality), and performing root-cause analysis on the two weakest fields.

---

## 1. Executive Summary & Deliverables

In production Gen AI extraction pipelines, reporting a single aggregate "document accuracy" score is misleading: an extraction pipeline could achieve 90% document pass rates while failing 100% of the time on critical fields like `tax_amount` or `due_date`.

On Day 3, we delivered:
1. **Field-Level Matching Engine ([`field_matcher.py`](../pipeline/field_matcher.py)):**
   - Applies domain-specific matching rules for each field type:
     - `invoice_id`: Exact string match after stripping `#`, `Invoice:`, and whitespace.
     - `invoice_date` & `due_date`: Normalized ISO `YYYY-MM-DD` calendar comparison.
     - `vendor_name` & `customer_name`: Fuzzy matching via RapidFuzz token set ratio ($\ge 85\%$).
     - `subtotal`, `tax_amount`, `total_amount`: Absolute numeric difference $\le 0.02$.
     - `currency` & `payment_terms`: Strict Enum equality.
     - True Negative Credit: Both ground truth and prediction correctly `null` = 1.0 (Correct).
2. **Automated Evaluator ([`field_evaluator.py`](field_evaluator.py)):**
   - Evaluates all 40 ground truth documents across 440 field instances.
   - Computes granular per-field accuracy percentages.
3. **Comprehensive Accuracy Report ([`ACCURACY_REPORT.md`](ACCURACY_REPORT.md)):**
   - Reports full 11-field accuracy breakdown.
   - Highlights overall field accuracy (**94.8%**).
   - Deep-dives into root cause and mitigation for the two weakest fields: `due_date` (80.0%) and `payment_terms` (80.0%).

---

## 2. Verification & Execution

Run the Day 3 Acceptance Verification Suite:
```bash
python week5/day3/verify_day3.py
```
*Expected: Confirms all 11 fields reported, matching rules validated, and ACCURACY_REPORT.md generated.*
