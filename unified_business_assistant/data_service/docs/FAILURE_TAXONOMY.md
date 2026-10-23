# Role B: Failure Taxonomy & Error Analysis Report

## 1. Executive Summary
As mandated by **Day 4 Deliverables** and **Acceptance Criterion 5**:
> *"A written failure taxonomy with counts exists (Ask which failure type was most common). Fix the largest category. Make answerable return false correctly."*

Every data query evaluated against the Role B Data Service is monitored, audited, and categorized into a formal failure taxonomy. Across our 40-question benchmark:
- **Baseline Accuracy**: 90.0% (36/40)
- **Largest Failure Category**: `OUT_OF_SCOPE_UNANSWERABLE` (3 occurrences)
- **Targeted Fix Applied**: Refined domain boundary filters in `schema_context.py` and expanded vocabulary coverage for product categories, inventory stock, and payment credentials.
- **Post-Fix Target**: 100.0% (40/40) accuracy across answerable and unanswerable boundaries.

---

## 2. Formal Failure Taxonomy Definitions

| Failure Category | Code | Description & Manifestation | Mitigation Strategy |
|---|---|---|---|
| **Out-of-Scope / Unanswerable** | `OUT_OF_SCOPE_UNANSWERABLE` | Query asks for metrics or entities absent from the database (e.g. employee medical data, stock tickers, wifi passwords, HR policies). | Dual-gate semantic filtering in `SchemaContextBuilder`: rejects queries before SQL generation, returning `answerable=false`. |
| **Wrong Join** | `WRONG_JOIN` | Joining on mismatched foreign keys (e.g., joining `customers` on `employee_id` instead of `customer_id`), missing `ON` conditions (Cartesian products), or circular joins. | Schema context explicitly details foreign key links; system prompt mandates explicit aliases; self-correction catches ambiguous column references. |
| **Wrong Aggregation** | `WRONG_AGGREGATION` | Missing `GROUP BY` when mixing aggregate and non-aggregate fields, or using `COUNT` when `SUM` is required. | AST validator checks aggregate queries; schema context provides explicit formulas for gross revenue and order sums. |
| **Hallucinated Column** | `HALLUCINATED_COLUMN` | LLM invents plausible but nonexistent column names (e.g. `client_name` instead of `company_name`, `total_revenue` instead of `total_amount`). | Compact schema context lists exact column names; deterministic heuristic and LLM self-correction loops repair column names using database errors. |
| **Ambiguous Question** | `AMBIGUOUS_QUESTION` | Question lacks sufficient business specificity (e.g., "Show best performing products" without specifying volume vs revenue). | Prompt instructs model to use standard business metrics (e.g. completed sales volume) with explicit ordering and limits. |
| **Syntax Error** | `SYNTAX_ERROR` | Malformed SQLite syntax or missing parentheses/commas. | AST parsing gate with `sqlglot` catches syntax errors before DB execution; self-correction engine feeds error back to model. |
| **Resource Timeout** | `TIMEOUT_RESOURCE` | Runaway Cartesian product or nested unindexed subquery taking > 5.0 seconds. | Connection manager enforces a hard 5.0-second execution deadline. |

---

## 3. Failure Counts & Distribution

From initial baseline run on [test_queries.json](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/unified_business_assistant/data_service/evaluation/test_queries.json):
```
Total Test Cases   : 40
Passed             : 36
Failed             : 4
Overall Accuracy   : 90.0%
----------------------------------------------------------------------
FAILURE TAXONOMY BREAKDOWN:
  • OUT_OF_SCOPE_UNANSWERABLE   :  3 ( 7.5%)
  • AMBIGUOUS_QUESTION          :  1 ( 2.5%)
  • WRONG_JOIN                  :  0 ( 0.0%)
  • WRONG_AGGREGATION           :  0 ( 0.0%)
  • HALLUCINATED_COLUMN         :  0 ( 0.0%)
  • SYNTAX_ERROR                :  0 ( 0.0%)
  • TIMEOUT_RESOURCE            :  0 ( 0.0%)
----------------------------------------------------------------------
Largest Category   : OUT_OF_SCOPE_UNANSWERABLE (3 occurrences)
```

---

## 4. Addressing the Largest Failure Category

### Root Cause Analysis
The largest failure category was **`OUT_OF_SCOPE_UNANSWERABLE`**, occurring in two directions:
1. **False Negative**: Queries `Q021` ("Software Licenses sold") and `Q027` ("Hardware stock") were valid data questions, but the domain filter did not recognize "licenses", "hardware", or "stock" as valid schema vocabulary, falsely classifying them as unanswerable.
2. **False Positive**: Query `Q040` ("confidential credit card numbers") asked for payment credentials. Because "credit card" was not explicitly caught by the negative regex filter, the model attempted to generate SQL instead of flagging it as unanswerable.

### Remediation Implemented
1. **Schema Vocabulary Expansion**:
   Added `hardware`, `software`, `license`, `licenses`, `stock`, `quantity`, `units`, `cost`, `margin`, `price`, and `channel` to `RECOGNIZED_TERMS`.
2. **Payment & PII Boundary Gate**:
   Added `credit card`, `card number`, `bank account`, `ssn`, `pin` to `UNSUPPORTED_DOMAINS` in `schema_context.py`.
3. **Channel Heuristic**:
   Added direct channel aggregation handling in `generator.py`.
