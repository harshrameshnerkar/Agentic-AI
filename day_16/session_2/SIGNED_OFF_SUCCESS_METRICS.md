# Day 16 - Session 2: Signed-Off Success Metrics Charter

**Document Version:** 1.0.0  
**Effective Date:** October 8, 2026  
**Review Cycle:** Monthly Reliability Review  
**Project:** OpsSentinel Autonomous Triage Copilot  
**Participants & Signatories:**  
- **Lead AI Systems Engineer:** Harsh Ramesh Nerkar  
- **VP of Cloud Infrastructure & Reliability:** Marcus Vance  

---

## 1. Executive Charter: Turning a Vague Ask into Measurable Targets

In Day 16 Session 1, the stakeholder expressed a high-level operational goal:
> *"Make our on-call incident response faster and stop fat-finger human errors under pressure."*

While clear in business intent, this request is too ambiguous for engineering execution. To build an autonomous production system, we translated this goal into **six mathematically verifiable target metrics with signed-off numeric thresholds**.

---

## 2. The 6 Signed-Off Success Metrics

| Metric ID | Metric Name | Definition & Measurement Formula | Human Baseline | Signed-Off Target | Hard Ceiling / Floor | Pass / Fail Criterion |
|:---:|---|---|:---:|:---:|:---:|:---:|
| **M1** | **Diagnostic Accuracy** | Percentage of incidents where the agent correctly identifies root cause and matching runbook: $$\text{Acc} = \frac{N_{\text{correct}}}{N_{\text{total}}} \times 100$$ | 82.4% | **$\ge 95.0\%$** | Floor: **92.0%** | $\text{Acc} \ge 95.0\%$ on 100-case golden suite |
| **M2** | **p95 Triage Latency** | Time elapsed from alert webhook ingestion to full root-cause brief delivery: $$T_{95} = \text{Percentile}_{95}(T_{\text{triage}})$$ | 78.5 mins | **$\le 60.0\text{ sec}$** | Ceiling: **$\le 90.0\text{ sec}$** | $T_{95} \le 90.0\text{s}$; p50 $\le 45.0\text{s}$ |
| **M3** | **Cost Per Triage Run** | Total LLM token inference cost + tool API costs per incident triage: $$C = \sum (\text{Tokens} \times \text{Rate}) + C_{\text{tools}}$$ | $134.50 (Human Toil) | **$\le \$0.10$ USD** | Ceiling: **$\le \$0.15$ USD** | Cost $\le \$0.15$ per incident triage |
| **M4** | **Unattended Destructive Writes** | Number of high-blast actions (restarts, scale-downs, cache flushes) executed without explicit human approval: $$N_{\text{unapproved\_tier3}}$$ | N/A (Manual) | **$0.0\%$ (Zero)** | Absolute: **$0$ Tolerance** | Any unapproved Tier-3 write = IMMEDIATE CI REJECT |
| **M5** | **Data Sensitivity & Secret Masking** | Percentage of credentials, API tokens, and PII masked before LLM context ingestion: $$\text{MaskRate} = \frac{N_{\text{masked\_secrets}}}{N_{\text{total\_secrets}}} \times 100$$ | High leak risk | **$100.0\%$** | Absolute: **$100.0\%$** | 0 unmasked secrets or PII in logs or prompt traces |
| **M6** | **MTTR Reduction Ratio** | Net reduction in Mean Time to Recovery compared to human baseline: $$\Delta\text{MTTR} = \frac{\text{MTTR}_{\text{human}} - \text{MTTR}_{\text{agent}}}{\text{MTTR}_{\text{human}}}$$ | Baseline | **$\ge 80.0\%$** | Floor: **$75.0\%$** | Average MTTR drops from 85 mins to $< 10$ mins |

---

## 3. Detailed Metric Specifications

### M1: Diagnostic Accuracy Bar ($\ge 95.0\%$)
- Evaluated against a curated, multi-modal **Golden Benchmark Evaluation Suite** (100 production incidents across CPU spikes, memory leaks, connection pool starvation, DNS outages, and bad canary deploys).
- To pass, the agent must output:
  1. The exact unhealthy Kubernetes pod/service name.
  2. The primary root cause category.
  3. The exact matching Standard Operating Procedure (SOP) identifier.
  4. Confidence score $\ge 0.85$.

### M2: Acceptable Latency Ceiling (p95 $\le 90.0\text{s}$, p50 $\le 45.0\text{s}$)
- Under production load, an alert must never stall waiting for sequential tool execution.
- Telemetry gathering across logs, metrics, Git commits, and topology must execute in parallel using `asyncio.gather`.
- Latency breakdown budget:
  - Ingestion & Routing: $< 2.0\text{ seconds}$.
  - Parallel Diagnostic Tool Dispatch: $< 25.0\text{ seconds}$.
  - SOP Semantic RAG Search: $< 5.0\text{ seconds}$.
  - LLM Synthesis & Hypothesis Formulation: $< 15.0\text{ seconds}$.
  - Total p50 Budget: **$< 47.0\text{ seconds}$**.

### M3: Cost Per Triage Ceiling ($\le \$0.15$ USD)
- Human on-call triage costs approximately **$134.50 USD per incident** (1.4 hours at $95/hr blended compensation).
- The Agentic AI Copilot must operate with strict economic efficiency:
  - Context compaction filter: prune redundant log lines from 50,000 lines to top 40 anomaly snippets.
  - Model tiering: Use lightweight fast reasoning models (e.g., Gemini 2.5 Flash / Claude 3.5 Haiku) for preliminary filtering ($\approx \$0.02$).
  - Complex multi-modal synthesis only when confidence is low ($\approx \$0.08$).
  - Hard budget ceiling: **$\$0.15$ USD per incident triage**.

### M4: Zero Unattended Destructive Operations ($0.0\%$)
- Zero tolerance for autonomous destructive writes.
- High-blast actions (Kubernetes pod delete/restart, service scaling, cache flushing) are intercepted by the **Human-in-the-Loop (HITL) Gateway**.
- Any execution bypassing this gate results in an immediate security audit failure.

### M5: Data Sensitivity & Secret Masking ($100.0\%$)
- Real-time regex and AST masking before prompt assembly:
  - `(?i)(password|secret|bearer|token|api_key|auth)[=:\s]+[A-Za-z0-9_\-\.]{8,}` $\rightarrow$ `[REDACTED_SECRET]`
  - Credit cards, Social Security Numbers, and client email addresses $\rightarrow$ `[REDACTED_PII]`

---

## 4. Formal Sign-Off & Agreement

By signing below, both engineering and reliability leadership agree that the above six metrics define the strict acceptance criteria for deploying the OpsSentinel Autonomous Triage Copilot into production environments.

```
================================================================================
                         FORMAL STAKEHOLDER SIGN-OFF
================================================================================

Lead AI Systems Engineer:
  Signature: Harsh Ramesh Nerkar
  Title:     Lead Autonomous AI Systems Architect
  Date:      October 8, 2026
  Status:    ACCEPTED & COMMITTED

VP of Cloud Infrastructure & Reliability:
  Signature: Marcus Vance
  Title:     VP of Infrastructure & Reliability Engineering
  Date:      October 8, 2026
  Status:    ACCEPTED & APPROVED FOR SYSTEM ARCHITECTURE
================================================================================
```
