# Day 18 - Session 4: Regression Suite

## 📌 Syllabus & Session Objectives
- **Session:** Day 18 - Session 4: Regression Suite
- **Topic:** Build Sprint 2 & Code Review — Automated CI Gate for Quality & Safety Preservation
- **Timebox:** 16:00 - 18:00 (2.0 hours)
- **What to Learn:** Building an automated regression suite that runs on every PR/commit, runs in < 60s, alerts on any drop in pass rate, and blocks merging if pass rate falls below threshold.
- **Task:** A regression test suite that runs in one command and fails loudly on a drop in pass rate.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Mentor (Dr. Elena Rostova).

---

## 🎯 Engineering Philosophy: Zero-Tolerance Regression

> *"A feature without a regression test is just technical debt waiting to explode.*  
> *"Sprint 2 code review fixed five critical issues. If any future commit reintroduces replay vulnerability,*  
> *"corrupts the audit chain, or slips past the PII scrubber, the CI pipeline must halt immediately.*  
> *"Our gate runs in under 1 second, evaluates 35 golden cases, and fails loudly with exit code 1 if pass rate falls below 95%."*  
> — **Dr. Elena Rostova, Principal AI Systems Architect**

---

## 📊 Regression Benchmark Results

| Metric | Target SLA | Benchmark Value | Status |
|---|:---:|:---:|:---:|
| **Golden Test Cases** | $\ge 35$ cases | **35 / 35 cases** | ✅ PASS |
| **Pass Rate** | $\ge 95.0\%$ | **100.0% (35/35)** | ✅ PASS |
| **Average Latency** | $\le 3,000$ ms | **44.97 ms** | ✅ PASS |
| **Max Latency (p99)** | $\le 5,000$ ms | **48.21 ms** | ✅ PASS |
| **Cost Per Query** | $\le \$0.0150$ | **$0.0028** | ✅ PASS |
| **Suite Wall-Clock Time** | $\le 60.0$ s | **1.57 s** | ✅ PASS |
| **Exit Code** | 0 (Clean) / 1 (Halt) | **0** | ✅ PASS |

---

## 📂 Deliverables & File Directory

- [regression_dataset_35.json](regression_dataset_35.json): 35 golden incident cases (30 domain baselines + 5 code-review regression bug cases).
- [run_regression_suite.py](run_regression_suite.py): One-command automated CI test runner with gate thresholds, exit code dispatch, and JSON artifact generation.
- [REGRESSION_SUITE_REPORT.md](REGRESSION_SUITE_REPORT.md): Detailed markdown report covering dataset taxonomy, baseline comparisons, and CI/CD integration steps.
- [REGRESSION_RUN_REPORT.json](REGRESSION_RUN_REPORT.json): Machine-readable execution report for CI artifact parsing.
- [main.py](main.py): CLI interface supporting `--summary`, `--report`, and `--ci-mode`.
- [test_regression_suite.py](test_regression_suite.py): 5 automated unit tests verifying runner exit codes, dataset validity, and threshold enforcement.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. Run the One-Command Regression Suite (CI Mode)
```bash
python day_18/session_4/run_regression_suite.py
```
*Expected: Prints color-coded benchmark summary and exits with code 0.*

### 2. Run Interactive CLI Summary
```bash
python day_18/session_4/main.py --summary
```

### 3. Run Test Suite
```bash
python day_18/session_4/test_regression_suite.py
```
*Expected: 5 unit tests passing with 100% assertions satisfied.*

### 4. Verify Non-Zero Exit on Gate Breach
```bash
python day_18/session_4/run_regression_suite.py --threshold 1.01
# Echo exit code (PowerShell: $LASTEXITCODE, Bash: $?) -> returns 1
```
