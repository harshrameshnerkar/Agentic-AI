# Day 2 - Session 3: Prompt Templates, Versioning & A/B Evaluation

Welcome to **Session 3** of **Day 2: Advanced Prompting & Structured Output**.

In this session, we transition from writing prompts as ad-hoc Python f-strings to building a **production-grade Prompt Management System** with externalized template files, variable injection, a **Prompt Registry**, and **A/B testing**.

---

## 🎯 What You Will Learn

1. **f-strings vs. Template Files**:
   - Why embedding multi-line prompts inside application code creates architectural debt and how template files decouple prompt engineering from software logic.
2. **Safe Variable Injection**:
   - Dynamically rendering placeholders without breaking JSON schemas or introducing delimiter collisions.
3. **Keeping Prompts in Version Control (Git)**:
   - Tracking prompt iterations with clear Git diffs, pull request reviews, and semantic tags (`v1`, `v2`, `production`).
4. **The Prompt Registry Pattern**:
   - Maintaining a metadata catalog (`registry.json`) mapping logical prompt names to versions, active deployment flags, and required schema variables.
5. **A/B Comparing Two Prompt Versions**:
   - Running side-by-side benchmark evaluations comparing baseline (v1) vs. engineered (v2) prompts across accuracy, JSON validity, and token behavior.

---

## 🧠 Core Architecture: f-Strings vs. Template Files

In early prototypes, developers typically write:
```python
# ❌ Hardcoded f-string approach (Anti-pattern in production)
def classify_email(email_text):
    prompt = f"Classify this email: {email_text} into Billing, Tech..."
    ...
```

### The Architectural Trade-Off

| Dimension | Hardcoded f-Strings | External Template Files (`prompts/`) |
| :--- | :--- | :--- |
| **Separation of Concerns** | ❌ Mixes LLM steering with Python business logic. | ✅ Prompts live in independent, dedicated `.txt`/`.j2` files. |
| **Git Diffs** | ❌ Modifying a prompt creates noise in Python commit logs. | ✅ Isolated, clean diffs focused solely on prompt phrasing. |
| **Collaboration** | ❌ Product managers / prompt engineers must edit Python code. | ✅ Non-programmers can safely edit prompt text without breaking code. |
| **A/B Testing & Rollbacks**| ❌ Requires messy `if/else` branching inside functions. | ✅ Swap prompt versions dynamically via `registry.render(name, version="v2")`. |
| **Validation** | ❌ Runtime KeyError if a variable name is mistyped. | ✅ Pre-execution schema checking verifies all required variables exist. |

---

## 📂 The Prompt Registry Pattern

Our prompt directory structure:
```text
day_02/session_3/
├── prompts/
│   ├── registry.json             # Manifest tracking versions, active tags, and required inputs
│   ├── email_classifier_v1.txt   # Version 1: Baseline naive prompt
│   └── email_classifier_v2.txt   # Version 2: Engineered prompt (delimiters, few-shot, JSON schema)
├── main.py                       # Registry loader & A/B testing benchmark
├── requirements.txt
└── README.md
```

### Manifest (`prompts/registry.json`)
```json
{
  "email_classifier": {
    "name": "email_classifier",
    "active_version": "v2",
    "versions": {
      "v1": {
        "file": "email_classifier_v1.txt",
        "description": "Baseline naive prompt without delimiters or few-shot examples",
        "required_variables": ["email_text"]
      },
      "v2": {
        "file": "email_classifier_v2.txt",
        "description": "Engineered prompt with XML delimiters, few-shot demonstrations, and strict JSON output",
        "required_variables": ["email_text"]
      }
    }
  }
}
```

### Python Registry Loader
```python
registry = PromptRegistry(PROMPTS_DIR)

# Render active production version
prompt = registry.render("email_classifier", version="active", email_text="I was charged twice.")

# Render specific experimental version for A/B testing
prompt_v1 = registry.render("email_classifier", version="v1", email_text="I was charged twice.")
```

---

## 🚀 How to Run the A/B Benchmark

```bash
cd day_02/session_3
python main.py
```

The script will:
1. Load `v1` and `v2` prompt templates from `prompts/`.
2. Execute both prompts sequentially across a benchmark suite of 8 customer support emails.
3. Compare both versions on:
   - **Classification Accuracy** (% matching ground truth).
   - **Strict JSON Output Rate** (% parseable as valid JSON objects).
   - **Reasoning Quality & Delimiter Protection**.
## 📈 Empirical A/B Benchmark Results

We executed the benchmark on `gemini-3.5-flash-lite` comparing `v1` vs. `v2` across the benchmark suite:

```text
===============================================================================================
 A/B COMPARATIVE EVALUATION REPORT: PROMPT V1 vs. PROMPT V2
===============================================================================================
Metric                              Version 1 (Naive)         Version 2 (Engineered)    Delta
-----------------------------------------------------------------------------------------------
Classification Accuracy             6/8 (75.0%)               8/8 (100.0%)              +25.0%
Strict JSON Format Rate             0/8 (0.0%)                8/8 (100.0%)              +100.0%
Role Setting & Delimiters           No (Vulnerable)           Yes (<email> tags)        Defensive
Few-Shot In-Context Learning        0 Examples                4 Demonstrations          Guided
===============================================================================================
Conclusion: Version 2 achieves strict JSON schema compliance and deterministic classification.
```

### 🔬 Failure Analysis of Version 1
1. **Zero Structured Output**: Without JSON mode and few-shot formatting, V1 output freeform conversational chat (e.g. *"This email is about a technical issue because Okta SAML failed..."*), scoring **0.0%** on automated parsing.
2. **Category Hallucination / Confusion**: On Email 3 (Okta SAML 500 Error) and Email 6 (Dark mode request), V1 confused the categories with Billing because there were no explicit definitions or negative constraints.
3. **Version 2 Resiliency**: With role setting, XML `<email>` tags, few-shot demonstrations, and strict JSON output, Version 2 achieved **100% accuracy** and **100% parseable JSON**.

