# Retrieval Evaluation & Chunk Size Benchmark

## 1. Summary
- **Date**: 2026-10-30
- **Test Set**: 15 labelled questions (`data/test_questions.json`) across 5 companies.
- **Embedding Model**: `all-MiniLM-L6-v2`
- **Selected Configuration**: **Config A (500 chars, 75 overlap)**
- **Recall@5**: **Document Recall@5 = 93.3%** | **Page Recall@5 = 93.3%**

## 2. Benchmark Results

| Metric | Config A (500 chars, 75 overlap) | Config B (1000 chars, 150 overlap) |
|---|---|---|
| Total Chunks | 3032 | 1661 |
| Document Recall@1 | 86.7% | 80.0% |
| Document Recall@3 | 86.7% | 86.7% |
| Document Recall@5 | 93.3% | 86.7% |
| Exact Page Recall@1 | 80.0% | 66.7% |
| Exact Page Recall@3 | 80.0% | 80.0% |
| Exact Page Recall@5 | 93.3% | 80.0% |

## 3. Reason for Choosing Config A (500 / 75)
1. **Higher Recall**: Config A achieved 93.3% Document Recall@5 and 93.3% Page Recall@5 compared to 86.7% and 80.0% for Config B. Top-1 page recall also improved from 66.7% to 80.0%.
2. **Model Window Fit**: `all-MiniLM-L6-v2` has a 256-token limit. Using 500-character chunks avoids token truncation and keeps embeddings focused on single policy rules rather than mixing multiple sections together.
3. **Page Provenance**: Smaller chunks map cleanly to individual sections on a page, which improves ranking scores on specific policy questions (such as filing deadlines or expense limits).

## 4. Per-Query Breakdown (Config A)

- **q01**: What is the paid maternity leave duration under Reckitt parental leave policy?
  - Expected: `reckitt_global_parental_leave_policy.pdf` (Pages [1, 2])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.6935

- **q02**: How many days of paid paternity leave are granted at Reckitt?
  - Expected: `reckitt_global_parental_leave_policy.pdf` (Pages [2])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7470

- **q03**: Who must chair or preside over the Internal Complaints Committee under Susan Electricals POSH policy?
  - Expected: `susan_electricals_posh_anti_sexual_harassment_policy.pdf` (Pages [3, 7])
  - Result: HIT | Doc Rank: 4, Page Rank: 4 | Top-1 Score: 0.5839

- **q04**: What is the time limit to file a complaint of sexual harassment under POSH in Susan Electricals?
  - Expected: `susan_electricals_posh_anti_sexual_harassment_policy.pdf` (Pages [4, 7])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.6295

- **q05**: What is the maximum single item expense that can be submitted via Navan without prior approval at GitLab?
  - Expected: `Gitlab Expense Policy.pdf` (Pages [3])
  - Result: HIT | Doc Rank: 1, Page Rank: 5 | Top-1 Score: 0.7458

- **q06**: What is GitLab's policy on team members expensing items on behalf of their managers?
  - Expected: `Gitlab Expense Policy.pdf` (Pages [1, 2, 3])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7100

- **q07**: How does an employee make a protected disclosure under the Whistleblower Vigil Mechanism policy at Susan Electricals?
  - Expected: `susan_electricals_vigil_mechanism_whistleblower_policy.pdf` (Pages [2, 3])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7349

- **q08**: What constitutes Unpublished Price Sensitive Information (UPSI) under Susan Electricals code of fair disclosure?
  - Expected: `susan_electricals_upsi_fair_disclosure_code.pdf` (Pages [1, 2])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7991

- **q09**: What are Google's seven AI principles for evaluating AI applications?
  - Expected: `Google AI principles operational guidelines.pdf` (Pages [2, 3])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7935

- **q10**: What are the rules regarding gifts and hospitality under Reckitt Third Party Code of Conduct?
  - Expected: `reckitt_third_party_code_of_conduct.pdf` (Pages [3])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.6947

- **q11**: What is the primary objective of Jayaswal Neco Corporate Social Responsibility (CSR) policy?
  - Expected: `jayaswal_neco_corporate_social_responsibility_policy.pdf` (Pages [1, 2])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.8682

- **q12**: What expectations are placed on suppliers regarding forced labour under Jayaswal Neco supplier code of conduct?
  - Expected: `jayaswal_neco_supplier_code_of_conduct.pdf` (Pages [1, 2])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7422

- **q13**: What are the core development values and principles at GitLab?
  - Expected: `Gitlab development principles.pdf` (Pages [1, 2, 6])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.7496

- **q14**: How does Reckitt define non-retaliation for employees raising ethical concerns in its Code of Conduct?
  - Expected: `reckitt_global_code_of_conduct.pdf` (Pages [1, 2, 6])
  - Result: HIT | Doc Rank: 1, Page Rank: 1 | Top-1 Score: 0.6654

- **q15**: What standards are required for human rights and fair treatment of workers under Reckitt Human Rights and Responsible Business Policy?
  - Expected: `reckitt_human_rights_and_responsible_business_policy.pdf` (Pages [1, 2, 3])
  - Result: MISS | Doc Rank: None, Page Rank: None | Top-1 Score: 0.6449
