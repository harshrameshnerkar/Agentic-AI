# Day 20 - Session 3: Sprint Retrospective

## 📌 Syllabus & Session Objectives
- **Session:** Day 20 - Session 3: Sprint Retrospective
- **Topic:** Demo, Retrospective & Final Assessment — Honest Estimation Variance & Technical Lessons
- **Timebox:** 14:00 - 16:00 (2.0 hours)
- **What to Learn:** What went well, what did not, where the estimates were wrong and why, what you would do differently. Reviewing the Sprint Board variance honestly rather than defending it.
- **Task:** A written retrospective including at least 3 specific mistakes and their lessons.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Mentor (Dr. Elena Rostova).

---

## 🎯 Engineering Retrospective Mindset

> *"A junior engineer defends their estimates and hides their mistakes.*  
> *"A senior engineer reviews their Sprint Board variance with curiosity and radical candor.*  
> *"Every wrong estimate reveals an architectural assumption that was not grounded in reality.*  
> *"The true output of an engineering sprint is not just working software, but the institutional wisdom*  
> *"crystallized from the mistakes made along the way."*  
> — **Dr. Elena Rostova, Principal AI Systems Architect**

---

## 📋 The 3 Specific Technical Mistakes & Lessons Learned

| # | Technical Area | Root Cause & Failure Mode | Architectural Lesson Learned |
|:---:|---|---|---|
| **1** | **HMAC Replay Window** | 300s timestamp window allowed captured approval tokens to be replayed. | Implemented `UsedNonceRegistry` with SHA-256 digests and TTL eviction for single-use guarantees. |
| **2** | **ReDoS Backtracking** | Nested quantifiers in PII scrubber regex risked exponential CPU exhaustion. | Bounded maximum input length to 100KB and pre-compiled linear-time regexes. |
| **3** | **Audit Hash Concurrency** | Parallel threads appending to audit log without locks forked the SHA-256 chain. | Serialized all audit log reads and appends using `threading.RLock()`. |

---

## 📂 Deliverables & File Directory

- [SPRINT_RETROSPECTIVE.md](SPRINT_RETROSPECTIVE.md): Full engineering retrospective covering wins, estimate variance, 3 mistakes, and future improvements.
- [RETROSPECTIVE_DATA.json](RETROSPECTIVE_DATA.json): Machine-readable variance data and technical mistake catalog.
- [retro_analyzer.py](retro_analyzer.py): Variance calculator and mistake aggregator.
- [main.py](main.py): Interactive CLI supporting `--summary`, `--variance`, `--mistakes`, and `--action-items`.
- [test_retrospective.py](test_retrospective.py): 5 automated unit tests validating retrospective data and lessons.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. View Sprint Estimate Variance Analysis
```bash
python day_20/session_3/main.py --variance
```

### 2. View 3 Specific Technical Mistakes & Lessons
```bash
python day_20/session_3/main.py --mistakes
```

### 3. View Next Sprint Action Items
```bash
python day_20/session_3/main.py --action-items
```

### 4. Run Test Suite
```bash
python day_20/session_3/test_retrospective.py
```
*Expected: 5 tests passing in < 0.01 seconds.*
