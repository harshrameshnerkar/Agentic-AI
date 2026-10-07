# Day 9 - Session 4: Cost & Latency Optimisation

## 1. Overview & Objectives

In production enterprise deployments, generative agents face two major economic and performance challenges:
1. **Compounding Inference Costs**: Complex system prompts, redundant queries, and uncompacted tool observations result in high token overhead and ballooning monthly API bills.
2. **Variable & High Tail Latencies**: Repetitive round-trips to large flagship models incur high p95/p99 tail latency, hurting user experience and backend throughput.

### Session Goals & Curriculum Targets
* **Cost Reduction**: Cut cost per query by **at least 40%** across a 30-query enterprise workload.
* **Pass Rate Parity**: Keep task pass rate within **2 percentage points** of the baseline unoptimized agent.
* **Latency Percentile Profiling**: Instrument and measure **p50 (median)**, **p90**, and **p95 (tail latency)**.
* **Core Architectural Patterns**:
  1. **Tiered Model Routing**: Small, fast, inexpensive model first (`gemini-3.1-flash-lite`); escalate to high-capacity model (`gemini-2.5-pro`) only upon failure or quality gate degradation.
  2. **Exact & Semantic Caching**: O(1) SHA-256 hash lookup for exact repeats + Entity/Discriminator-aware Dice similarity for semantic paraphrases (0 tokens, sub-millisecond latency).
  3. **Prompt Compression**: Lean system prompt (~75 tokens) eliminating verbose philosophical instructions and redundant few-shot examples (~950 tokens).
  4. **Observation Compaction**: Minifying verbose JSON payloads from tools (tabular pipe/CSV rows and filtered log excerpts).

---

## 2. Architecture & Optimization Pillars

```
+-----------------------------------------------------------------------------------+
|                            Incoming Enterprise Query                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
               +---------------------------------------------------+
               |               LAYER 1: HYBRID CACHE               |
               |  1. Exact Cache (SHA-256 normalized digest)       |
               |  2. Semantic Cache (Discriminator-safe Similarity)|
               +---------------------------------------------------+
                         /                               \
               [Hit: 0 Tokens, <2ms]             [Miss: New Query]
                       /                                   \
                      v                                     v
         +--------------------------+         +-------------------------------+
         | Return Cached Response   |         |  LAYER 2: PROMPT COMPRESSION  |
         | (100% Cost & Latency Cut)|         |  • Lean System Prompt (75 tok)|
         +--------------------------+         |  • Compact Tool Schemas       |
                                              +-------------------------------+
                                                              |
                                                              v
                                              +-------------------------------+
                                              |   LAYER 3: MODEL ROUTER       |
                                              |   Tier 1: gemini-3.1-flash-lite
                                              +-------------------------------+
                                                              |
                                                 [Tool Call Generated]
                                                              |
                                                              v
                                              +-------------------------------+
                                              | LAYER 4: OBSERVATION COMPACTOR|
                                              | • Tabular CSV format for DB   |
                                              | • Truncated error-only logs   |
                                              +-------------------------------+
                                                              |
                                                              v
                                              +-------------------------------+
                                              |       QUALITY GATE CHECK      |
                                              |  Valid answer?                |
                                              +-------------------------------+
                                                     /                 \
                                                [Yes]             [No / Error]
                                                 /                       \
                                                v                         v
                                    +--------------------+   +--------------------+
                                    | Complete & Cache   |   | Escalate to Tier 2 |
                                    | Store in Layer 1   |   | (gemini-2.5-pro)   |
                                    +--------------------+   +--------------------+
```

---

## 3. Deep Dive into Implemented Techniques

### A. Tiered Model Routing (`model_router.py`)
- **Tier 1 (Small & Fast)**: `gemini-3.1-flash-lite` ($0.075 / 1M input, $0.30 / 1M output). Handles 95%+ of typical tool calls and reasoning queries with low latency.
- **Tier 2 (High Capacity)**: `gemini-2.5-pro` ($1.25 / 1M input, $5.00 / 1M output). Used strictly as a fallback when Tier 1 generates empty content, fails schema constraints, or exhausts execution retries.
- **Cost Differential**: Routing to Tier 1 cuts token inference cost by **~16.7x** relative to invoking the Pro model directly.

### B. Exact & Semantic Caching (`cache_manager.py`)
- **Exact Cache**:
  - Normalizes whitespace and casing, generates a SHA-256 hash digest.
  - O(1) hash table lookup. Execution time: $<0.5\text{ ms}$, cost: $\$0.00$.
- **Semantic Intent Cache**:
  - Tokenizes, stems, and filters non-informative stopwords.
  - **Discriminator Safety**: Extracts critical identifying parameters (e.g., `Standard` vs `Enterprise` account tiers, SKU identifiers like `SKU-SWITCH-24`, Order IDs like `ORD-501`). If two queries contain conflicting discriminators, the match is rejected immediately to prevent semantic collisions.
  - Computes Dice and Overlap coefficients ($\ge 0.55$ threshold) to match natural paraphrases without false positives.

### C. Prompt Compression (`prompt_optimizer.py`)
- **Baseline Prompt**: 950+ tokens containing verbose philosophical rules ("strive to provide exhaustive... consider all aspects of relational calculus...") and 3 lengthy few-shot examples.
- **Optimized Prompt**: 75 tokens containing only essential behavioral directives and tool descriptions.
- **Observed Savings**: Eliminates ~875 tokens on *every single LLM turn*, directly slashing input token bills.

### D. Observation Compaction (`prompt_optimizer.py`)
- Standard tool output returns indented JSON payloads with repeating keys (`[{"customer_id": "...", "name": "..."}, ...]`).
- `ObservationCompactor` serializes database rows as compact CSV headers and pipe/comma-separated records, cutting observation token usage by **60% to 75%**.
- Log reader filters `/var/log/syslog` to only error and warning events, removing startup and info lines.

---

## 4. Workload Benchmark Composition (`workload.py`)

A representative 30-case enterprise workload simulates production traffic:
1. **18 Unique Queries (Q-01 to Q-18)**:
   - Database operations (customer tiers, orders, inventory lookups).
   - Knowledge base SOP searches (JWT rotation, on-call SLAs, API rate limits).
   - Arithmetic computations (MRR to ARR, profit margin percentages, batch pricing).
   - System log analysis (connection pool exhaustions, error diagnosis).
2. **6 Exact Repeats (Q-19 to Q-24)**:
   - Identical queries evaluating Exact Cache hits (0 tokens, instant response).
3. **6 Semantic Repeats (Q-25 to Q-30)**:
   - Paraphrased re-queries evaluating Semantic Intent Cache hits.

---

## 5. Statistical Latency Percentile Methodology (`cost_tracker.py`)

Unlike simple average (mean) latency—which masks long delays experienced by users—production observability mandates percentile tracking:
- **p50 (Median)**: 50% of requests finish faster than this latency threshold.
- **p90**: Represents typical performance for high-traffic operations.
- **p95**: Tail latency capturing standard worst-case execution under peak conditions.
- **p99**: Extreme tail latency due to cold-starts or network retries.

All metrics are calculated using `numpy.percentile` over the run history.

---

## 6. Empirical Performance Scorecard

The head-to-head benchmark run across the 30-case enterprise workload produced the following empirical scorecard:

| Performance Metric | Baseline (Unoptimized) | Optimized Agent | Optimization Delta |
| :--- | :--- | :--- | :--- |
| **Total Tokens Consumed** | 63,459 | 12,406 | **-80.5% Tokens** |
| **Total Dollar Cost (USD)** | $0.005904 | $0.001165 | **-80.3% Cost** |
| **Cost per Query (USD)** | $0.000197 | $0.000039 | **-80.3% Cheaper** |
| **Task Pass Rate (%)** | 100.0% (30/30) | 100.0% (30/30) | **Δ 0.0% pts (Full Parity)** |
| **Cache Hit Rate (%)** | 0.0% (No Caching) | 40.0% (12/30) | **+40.0% Cached** |
| **Median Latency (p50)** | 6,265.2 ms | 3,327.8 ms | **-2,937.4 ms (~47% Faster)** |
| **90th Percentile (p90)** | 9,184.7 ms | 7,235.2 ms | **-1,949.5 ms** |
| **95th Percentile (p95)** | 10,076.5 ms | 8,866.6 ms | **-1,209.9 ms** |
| **Mean Request Latency** | 6,990.6 ms | 4,482.6 ms | **-2,508.0 ms** |

---

## 7. Curriculum Success Verification

1. **Cost Reduction Target ($\ge 40.0\%$)**:
   - **Achieved: 80.3% cost reduction** (Target Exceeded by 40.3 percentage points) $\rightarrow$ **PASS**
2. **Pass Rate Parity Target ($\le 2.0\%$ difference)**:
   - **Achieved: $\Delta$ 0.0% percentage points** (100.0% vs 100.0% task accuracy) $\rightarrow$ **PASS**
3. **Statistical Latency Percentiles**:
   - Instrumented and measured median ($p50$), $p90$, tail ($p95$), and mean request latencies.

---

## 8. File Structure & How to Run

```
day_09/session_4/
├── .env                  # API endpoint and model keys
├── requirements.txt      # Dependencies (openai, python-dotenv, pydantic, numpy)
├── tools.py              # Operational tools (DB, docs, calculator, logs)
├── prompt_optimizer.py   # Bloated prompt vs compressed prompt & ObservationCompactor
├── cache_manager.py      # Exact SHA-256 cache & Semantic intent cache
├── model_router.py       # Tier 1 small model first + Quality gate escalation
├── workload.py           # 30-case enterprise workload dataset
├── cost_tracker.py       # Token accounting, tier costing & percentile stats engine
├── baseline_agent.py     # Unoptimized baseline agent
├── optimized_agent.py    # Production cost-optimized agent
├── main.py               # Master comparative benchmark runner
└── README.md             # Architecture documentation & audit report
```

### Running the Benchmark
```bash
python main.py
```
