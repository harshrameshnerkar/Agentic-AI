# Task 5 - Day 3: Field-Level Accuracy Benchmark Report

> **Dataset:** 40 Hand-Keyed Commercial Invoices (25 text PDFs, 10 scanned PDFs, 5 images)
> **Overall Field Accuracy:** **94.8%** (across 440 field instances)

---

## 1. Granular Field-Level Accuracy Table

| # | Field Name | Target Type | Evaluated | Correct | Accuracy (%) | Status |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 1 | `invoice_id` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 2 | `invoice_date` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 3 | `due_date` | string/date/decimal | 40 | 32 | **80.0%** | ⚠️ WEAK |
| 4 | `vendor_name` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 5 | `vendor_tax_id` | string/date/decimal | 40 | 36 | **90.0%** | ✅ STRONG |
| 6 | `customer_name` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 7 | `currency` | string/date/decimal | 40 | 37 | **92.5%** | ✅ STRONG |
| 8 | `subtotal` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 9 | `tax_amount` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 10 | `total_amount` | string/date/decimal | 40 | 40 | **100.0%** | ✅ STRONG |
| 11 | `payment_terms` | string/date/decimal | 40 | 32 | **80.0%** | ⚠️ WEAK |

---

## 2. In-Depth Root Cause Analysis: Two Weakest Fields

### 🔻 Weakest Field 1: `due_date` (80.0% Accuracy)
- **Root Cause:** Due dates in commercial B2B invoicing are frequently communicated via dynamic terms (e.g. *'Net 30'*, *'Due Upon Receipt'*) rather than an explicit printed calendar due date. Per our strict policy in `FIELD_SPECIFICATION.md`, the model is forbidden from extrapolating calendar dates from terms. When OCR misses faint letterhead dates on scanned documents, `due_date` falls back to `null`.
- **Engineering Mitigation:** In Day 4 confidence routing, documents with missing due dates but explicit payment terms are flagged with intermediate confidence, allowing downstream ERP rules engines to compute canonical calendar due dates deterministically.

### 🔻 Weakest Field 2: `payment_terms` (80.0% Accuracy)
- **Root Cause:** Commercial invoices express payment terms with diverse freeform phrasing (*'Net 30 days'*, *'Due Upon Receipt'*, *'Payable within 15 days of invoice'*, or completely absent on retail/walk-in receipts). Mapping natural language phrases to strict uppercase Enums can drop non-standard terms to `UNKNOWN`.
- **Engineering Mitigation:** Expanded the Pydantic `payment_terms` validator with fuzzy phrase normalizers (e.g. detecting '30' or 'RECEIPT') to map varied phrasing cleanly while defaulting gracefully to `UNKNOWN`.

---

## 3. Sensible Matching Rules Applied

1. **`invoice_id`:** Exact match after stripping `#`, `Invoice:`, and whitespace.
2. **`invoice_date` & `due_date`:** Normalized ISO `YYYY-MM-DD` calendar comparison.
3. **`vendor_name` & `customer_name`:** Fuzzy string matching via RapidFuzz token set ratio (>= 85%).
4. **`subtotal`, `tax_amount`, `total_amount`:** Numeric difference <= 0.02 units.
5. **`currency` & `payment_terms`:** Standardized Enum equality.
6. **True Negative Credit:** When both ground truth and prediction are correctly absent (`null`), it is scored as a valid match.