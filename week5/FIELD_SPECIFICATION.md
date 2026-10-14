# Field Specification: Commercial B2B/B2C Invoices

This document establishes the official extraction contract, typing schema, normalization rules, and missing value policies for the **Task 5 Document Extraction Pipeline**.

---

## 1. Domain & Scope

- **Document Type:** Commercial Invoices (Tax Invoices, Service Bills, Commercial Purchases, Hardware/Software Subscriptions).
- **Extraction Target:** Exactly 11 structured fields (10 attributes + 1 categorization enum).
- **Core Principle:** **High Precision over Speculative Hallucination**. If a field is not printed or is visually indeterminable, the model must return explicit `null` (or enum `UNKNOWN`). It must **never** extrapolate, synthesize, or invent values.

---

## 2. Field Specification Summary Table

| # | Field Name | Target Type | Example Values | What to Do When Missing | Normalization Rule |
|---|------------|-------------|----------------|-------------------------|---------------------|
| 1 | `invoice_id` | `string` | `"INV-2024-1001"`, `"BILL-202401"` | **`null`** (Flagged as critical anomaly) | Strip prefix `"Invoice #:"`, trim whitespace |
| 2 | `invoice_date` | `string (ISO Date)` | `"2024-01-15"` | **`null`** (Never default to today) | Convert to ISO 8601 `YYYY-MM-DD` |
| 3 | `due_date` | `string (ISO Date)` | `"2024-02-14"` | **`null`** (Do NOT compute from terms) | Convert to ISO 8601 `YYYY-MM-DD` |
| 4 | `vendor_name` | `string` | `"Apex Cloud Systems Inc."` | **`null`** (Immediate review route) | Clean trailing punctuation, keep legal suffixes |
| 5 | `vendor_tax_id`| `string` | `"US-84-2910394"`, `"GB-928374615"` | **`null`** (Common on US B2C receipts) | Strip `"Tax ID:"` / `"VAT:"`, keep alphanumeric & hyphens |
| 6 | `customer_name`| `string` | `"OmniCorp Global Inc."` | **`null`** (Cash / walk-in purchases) | Strip `"Bill To:"` label, trim whitespace |
| 7 | `currency` | `string (ISO 4217)`| `"USD"`, `"EUR"`, `"GBP"`, `"CAD"`, `"INR"` | **`USD`** if US address, else **`null`** | 3-letter uppercase code (e.g., `$` -> `USD`, `€` -> `EUR`) |
| 8 | `subtotal` | `decimal / float` | `1200.00`, `4500.50` | **`null`** (Unless zero-tax invoice) | Float / Decimal with 2 decimal places |
| 9 | `tax_amount` | `decimal / float` | `99.00`, `0.00` | **`0.00`** if exempt, else **`null`** | Float / Decimal with 2 decimal places |
| 10| `total_amount` | `decimal / float` | `1299.00`, `5355.00` | **`null`** (Critical blocker) | Float / Decimal with 2 decimal places |
| 11| `payment_terms`| `enum` | `"NET_30"`, `"DUE_ON_RECEIPT"` | **`UNKNOWN`** | Standardized uppercase Enum value |

---

## 3. Deep-Dive Field Rules (Mentor Verification Reference)

### Field 1: `invoice_id`
- **Definition:** The unique reference number assigned to the transaction by the billing vendor.
- **What Counts:** Any identifier explicitly labeled as `Invoice Number`, `Invoice #`, `Inv No.`, `Bill #`, or `Tax Invoice #`.
- **Missing Value Rule:** If absent, illegible, or torn off, return **`null`**.
  > *Why:* Without an invoice number, financial ERP systems cannot deduplicate or reconcile payments. Synthesizing an ID is strictly forbidden.
- **Scoring Match Rule:** Exact match after stripping whitespace and common labels (`#`, `Invoice:`, `No.`).

### Field 2: `invoice_date`
- **Definition:** The official date the invoice was generated, issued, or rendered.
- **What Counts:** The explicit invoice issue date (e.g. `15/01/2024`, `January 15, 2024`, `2024-01-15`, `15-Jan-2024`).
- **Missing Value Rule:** If absent, return **`null`**.
  > *Why:* Invoicing systems must not assume the scanning date or current date represents the transaction date for tax and accounting periods.
- **Scoring Match Rule:** Normalized date comparison (`YYYY-MM-DD`). `01/15/2024` and `2024-01-15` evaluate as identical matches.

### Field 3: `due_date`
- **Definition:** The deadline date by which full payment must be received by the vendor.
- **What Counts:** An explicit printed calendar due date (e.g. `Due Date: 2024-02-14`, `Payment Due: Feb 14, 2024`).
- **Missing Value Rule:** If no explicit calendar due date is printed on the document, return **`null`**.
  > *Why:* Even if "Payment Terms: Net 30" is printed, the extraction layer extracts only explicit document facts. Date addition business logic belongs to downstream ERP payment engines, not the vision/OCR model.
- **Scoring Match Rule:** Normalized date comparison (`YYYY-MM-DD`).

### Field 4: `vendor_name`
- **Definition:** The legal business name or registered trade name of the entity billing the client.
- **What Counts:** The company name in the top letterhead, logo block, or "From:" / "Remit To:" section.
- **Missing Value Rule:** If absent or unrecognizable, return **`null`**.
- **Scoring Match Rule:** Fuzzy string similarity (RapidFuzz token set ratio $\ge 88\%$) to tolerate minor OCR punctuation or spacing artifacts (e.g. `Apex Cloud Systems Inc` vs `Apex Cloud Systems, Inc.`).

### Field 5: `vendor_tax_id`
- **Definition:** The official tax registration or business identification number issued by a tax authority (e.g., US EIN, UK/EU VAT Number, Indian GSTIN, Canadian BN).
- **What Counts:** Explicit alphanumeric strings labeled as `VAT`, `Tax ID`, `EIN`, `GSTIN`, `ABN`, `RFC`.
- **Missing Value Rule:** Return **`null`** if omitted.
  > *Why:* Many small businesses, contractors, or US state-level B2C service invoices do not list a tax ID. Absence is standard business practice in many jurisdictions.
- **Scoring Match Rule:** Exact alphanumeric match (case-insensitive, ignoring punctuation like spaces and hyphens).

### Field 6: `customer_name`
- **Definition:** The person, business, or department to whom the goods/services were billed.
- **What Counts:** The entity specified under `Billed To:`, `Sold To:`, `Client:`, `Invoice To:`, or `Customer:`.
- **Missing Value Rule:** Return **`null`** if the document is a generic cash receipt, walk-in voucher, or unaddressed counter sale.
- **Scoring Match Rule:** Fuzzy string similarity (RapidFuzz token set ratio $\ge 85\%$).

### Field 7: `currency`
- **Definition:** The ISO 4217 standard 3-letter currency code representing monetary values on the document.
- **What Counts:** Standard currency codes (`USD`, `EUR`, `GBP`, `CAD`, `INR`) or unambiguous symbols (`$`, `€`, `£`, `C$`, `₹`).
- **Missing Value Rule:** If no currency symbol or text code appears anywhere on the invoice, infer `USD` only if the vendor address is in the USA. If completely ambiguous or multiple contradictory currencies appear, return **`null`**.
- **Scoring Match Rule:** Exact uppercase string match (`USD` == `USD`).

### Field 8: `subtotal`
- **Definition:** The total monetary amount before taxes, duties, and discounts.
- **What Counts:** The amount printed beside `Subtotal`, `Total Net`, `Net Amount`, or calculated base sum.
- **Missing Value Rule:** If there is no separate subtotal row:
  - If `tax_amount == 0.00` and `total_amount` is present, `subtotal` is equal to `total_amount`.
  - Otherwise, return **`null`**.
- **Scoring Match Rule:** Numeric difference $\le 0.02$ units.

### Field 9: `tax_amount`
- **Definition:** The total cumulative tax charged on the invoice (Sales Tax, VAT, GST).
- **What Counts:** The sum of tax lines, or line labeled `Tax`, `VAT (19%)`, `Sales Tax`, `GST (18%)`.
- **Missing Value Rule:**
  - If the invoice states `Tax: $0.00`, `0% Tax`, `Tax Exempt`, or has no tax line on an exempt transaction where `total_amount == subtotal`, record as **`0.00`**.
  - If the tax is omitted and cannot be confirmed as zero, return **`null`**.
- **Scoring Match Rule:** Numeric difference $\le 0.02$ units.

### Field 10: `total_amount`
- **Definition:** The final, binding gross monetary amount payable by the debtor.
- **What Counts:** The amount labeled `Total Due`, `Total Amount`, `Invoice Total`, `Grand Total`, `Balance Due`.
- **Missing Value Rule:** Return **`null`**.
  > *Why:* This is a mission-critical field. In downstream accounts payable, an invoice without a valid total cannot be approved for automated payment.
- **Scoring Match Rule:** Numeric difference $\le 0.02$ units.

### Field 11: `payment_terms`
- **Definition:** The commercial credit agreement governing when payment must be executed.
- **Allowed Enum Values:**
  - `DUE_ON_RECEIPT`: Payable immediately upon document delivery.
  - `NET_15`: Payable within 15 calendar days.
  - `NET_30`: Payable within 30 calendar days.
  - `NET_45`: Payable within 45 calendar days.
  - `NET_60`: Payable within 60 calendar days.
  - `PREPAID`: Paid in advance / balance zero.
  - `OTHER`: A non-standard credit term (e.g. `50% deposit, balance on completion`).
  - `UNKNOWN`: No payment terms were stated or discernible.
- **Missing Value Rule:** Return **`UNKNOWN`**.
- **Scoring Match Rule:** Exact Enum equality.

---

## 4. Typical Mentor Verification Questions & Answers

### Q1: "What happens when `due_date` is missing from the document?"
> **Answer:** It must be extracted as `null`. We explicitly do NOT calculate `invoice_date + 30 days` even if "Net 30" is present. The document extraction pipeline's responsibility is high-fidelity factual extraction. Downstream ERP systems apply business rules; the extraction model must never hallucinate dates that do not exist in the source document.

### Q2: "What happens when `vendor_tax_id` is missing?"
> **Answer:** It is recorded as `null`. In the United States and many global B2C / consulting arrangements, vendors are not legally required to publish their EIN or SSN on standard billing invoices. Treating missing tax ID as a system failure would cause massive false-positive rejections.

### Q3: "What happens when `tax_amount` is missing?"
> **Answer:** If the document explicitly states zero tax, exemption, or has no tax line and the total matches the subtotal, it is recorded as `0.00`. If the document has a discrepancy between subtotal and total without an explicit tax line, it is recorded as `null` and routed for human review.
