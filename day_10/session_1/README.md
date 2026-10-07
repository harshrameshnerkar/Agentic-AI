# Day 10 - Session 1: Capstone Assembly

## 1. Executive Summary & Defending Scope Choice

In **Day 10 Session 1**, the objective is to synthesize all core agentic design patterns built across the curriculum—**RAG, Tools, Memory, Guardrails, and Evaluation**—into one coherent, production-grade system and get it passing an automated test suite.

### Chosen Scope: OpsSentinel AI (Autonomous Enterprise SRE & Incident Response)
* **Why this scope is defensible**:
  1. **High Consequence & Security Sensitivity**: In modern DevOps and SRE, agents have access to critical systems (microservices, databases, logs). Autonomous systems cannot be toy demonstrations—they require strict blast-radius controls, role-based authorization, and PII protection.
  2. **Multi-Modal Requirements**: Ops incident response naturally requires:
     - **RAG**: Accessing complex technical runbooks, disaster recovery playbooks, and SLAs.
     - **Tools**: Running diagnostic queries, reading host/container logs, evaluating arithmetic budgets, and triggering alerts.
     - **Memory**: Remembering the active incident ticket, user identity, permission level, and past dialogue history across turns.
     - **Guardrails**: Blocking prompt injections (e.g. malicious log poisoning or adversarial user inputs), redacting IPs/passwords, and blocking destructive actions without approval tokens.
     - **Evaluation**: Verifying that both the tool trajectory and final answer meet rigorous factual and security criteria.
  3. **High Feasibility**: Highly realistic mock telemetry, virtual filesystem logs, and operational databases provide deterministic testing without fragile external cloud infrastructure dependencies.

---

## 2. End-to-End System Architecture

```
                                  [User Request]
                                         |
                                         v
               +---------------------------------------------------+
               |             LAYER 1: INPUT GUARDRAIL              |
               |  • Prompt Injection Scanner (Jailbreak Defense)   |
               |  • PII & Secret Redactor (IPs, Emails, API Keys)  |
               +---------------------------------------------------+
                         /                               \
                 [Malicious / Jailbreak]            [Allowed & Sanitized]
                       /                                   \
                      v                                     v
         +--------------------------+         +-------------------------------+
         | Immediate Refusal Block  |         |   LAYER 2: MEMORY INJECTION   |
         | (0 LLM Tokens, <1ms)     |         | • Long-Term Entity Store      |
         +--------------------------+         |   (User, Role, Active Ticket) |
                                              | • Short-Term Dialogue Buffer  |
                                              +-------------------------------+
                                                              |
                                                              v
                                              +-------------------------------+
                                              |  LAYER 3: REASONING & TOOLS   |
                                              |  • gemini-3.1-flash-lite      |
                                              |  • Function Calling Loop      |
                                              +-------------------------------+
                                                              |
                                                    [Tool Call Emitted]
                                                              |
                                                              v
                                              +-------------------------------+
                                              | LAYER 4: BLAST-RADIUS GATE    |
                                              | • Read-Only Tools: ALLOW      |
                                              | • Destructive Tools: GATE     |
                                              |   (Role check & Auth Token)   |
                                              +-------------------------------+
                                                     /                 \
                                                [Approved]          [Denied]
                                                   /                     \
                                                  v                       v
                                        +-------------------+   +--------------------+
                                        | Execute Tool      |   | Permission Denied  |
                                        | (DB/Logs/RAG/Ops) |   | Error Observation  |
                                        +-------------------+   +--------------------+
                                                   \                     /
                                                    \                   /
                                                     v                 v
                                              +-------------------------------+
                                              |  LAYER 5: OUTPUT SANITIZER    |
                                              |  • Credential Leak Scanner    |
                                              |  • Memory Buffer Update       |
                                              +-------------------------------+
                                                              |
                                                              v
                                                    [Final Safe Response]
```

---

## 3. Subsystem Implementation Breakdown

### 1. RAG Engine (`rag_engine.py`)
- Stores enterprise SOPs and disaster recovery runbooks:
  - `RUNBOOK-01`: Postgres Database Connection Pool Exhaustion SOP.
  - `RUNBOOK-02`: Kubernetes Ingress 502/504 Gateway Timeout Triage.
  - `RUNBOOK-03`: Redis Cache Cluster Failover & Eviction Playbook.
  - `RUNBOOK-04`: Sev-1 Emergency Incident Escalation Protocol.
  - `RUNBOOK-05`: Microservice Deployment Rollback & Canary Abort Procedure.
  - `RUNBOOK-06`: API Gateway Rate Limiting & Quota Management Policy.
- Scores query terms against document content, curated keywords, and titles with weighted relevance ranking.
- Generates strict citations (`[RUNBOOK-XX: Title]`) to ground all operational advice.

### 2. Operational Tools (`tools.py`)
- **Read-Only Diagnostic Tools**:
  - `query_telemetry_db`: Filters relational database tables (`services`, `incidents`, `clusters`).
  - `read_system_logs`: Reads logs (`/var/log/k8s/ingress.log`, `/var/log/postgres.log`, `/var/log/auth.log`).
  - `calculate_metrics`: Evaluates exact arithmetic for error budgets, availability uptime, and memory ratios.
  - `search_runbooks`: Queries technical runbooks via RAG engine.
- **Privileged Destructive Tools**:
  - `restart_service`: Dispatches rolling pod restarts. Guarded by approval token.
  - `rollback_deployment`: Reverts container deployment to target stable image version.
  - `dispatch_emergency_alert`: Broadcasts incident notification to Slack war room / PagerDuty.

### 3. Memory Subsystem (`memory_manager.py`)
- **Short-Term Dialogue Buffer**: Bounded sliding window buffer preserving conversational turns and tool observations across interactions.
- **Long-Term Entity Store**: Tracks persistent session context across turns:
  - Current authenticated user: `Sarah Conner`
  - Assigned security role: `Admin` (or `Auditor` / `Engineer`)
  - Target environment: `production` in `us-east-1`
  - Active incident ticket: `INC-801`
  - Emergency approval token: `AUTH-OPS-APPROVE-2026`

### 4. Security Guardrails & Blast-Radius Control (`guardrails.py`)
- **Input Guardrail**: Scans queries for direct/indirect prompt injection, jailbreaks ("DAN mode", "developer mode", "delete all tables", "ignore all instructions"). Immediately halts execution.
- **PII & Secret Redaction**: Anonymizes IPv4 addresses (`[REDACTED_IPV4]`), emails (`[REDACTED_EMAIL]`), and API keys prior to LLM submission.
- **Blast-Radius Gate**:
  - Automatically permits read-only operations.
  - Rejects destructive operations if caller has read-only role (`Auditor`).
  - Rejects destructive operations if caller fails to provide the required authorization token.
- **Output Guardrail**: Sanitizes output strings, preventing accidental leakage of private keys or bearer tokens.

### 5. Unified Capstone Agent (`capstone_agent.py`)
- Glues the 4 subsystems into a single multi-turn execution loop with rate-limit backoff on 429 quota exhaustion.

---

## 4. Test Suite Composition (`test_suite.py`)

A 20-case test suite thoroughly verifies all functional and security capabilities:
1. **Knowledge RAG & SOP Grounding (TC-01 to TC-04)**: Checks runbook retrieval, exact SOP steps, and document citations.
2. **Diagnostic Tools & Arithmetic (TC-05 to TC-08)**: Verifies DB queries, log inspections, and uptime arithmetic.
3. **Conversational Memory & Entity Tracking (TC-09 to TC-12)**: Tests entity recall of username, role, active ticket, and multi-turn referential continuity.
4. **Security Guardrails & PII Sanitization (TC-13 to TC-16)**: Validates prompt injection blocking, system prompt exfiltration defense, and IP address redaction.
5. **Blast-Radius Access Gates & Remediation (TC-17 to TC-20)**: Tests role-based denial for Auditor, missing token rejection, authorized restart execution, and emergency alert dispatching.

---

## 5. Execution Instructions

To run the full automated test suite:
```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_10\session_1
python main.py
```

---

## 6. Empirical Evaluation Scorecard

The full 20-case end-to-end benchmark run produced the following results:

```
+----------+--------------------------+--------------------------------+------------+----------+----------+
| Case ID  | Category                 | Tools Called                   | Traj       | Ans      | Verdict  |
+----------+--------------------------+--------------------------------+------------+----------+----------+
| TC-01    | Knowledge_RAG            | search_runbooks                | OK         | OK       | PASS     |
| TC-02    | Knowledge_RAG            | search_runbooks                | OK         | OK       | PASS     |
| TC-03    | Knowledge_RAG            | search_runbooks                | OK         | OK       | PASS     |
| TC-04    | Knowledge_RAG            | search_runbooks                | OK         | OK       | PASS     |
| TC-05    | Diagnostic_Tools         | query_telemetry_db             | OK         | OK       | PASS     |
| TC-06    | Diagnostic_Tools         | read_system_logs               | OK         | OK       | PASS     |
| TC-07    | Diagnostic_Tools         | query_telemetry_db             | OK         | OK       | PASS     |
| TC-08    | Diagnostic_Tools         | calculate_metrics              | OK         | OK       | PASS     |
| TC-09    | Conversational_Memory    | none                           | OK         | OK       | PASS     |
| TC-10    | Conversational_Memory    | query_telemetry_db             | OK         | OK       | PASS     |
| TC-11    | Conversational_Memory    | none                           | OK         | OK       | PASS     |
| TC-12    | Conversational_Memory    | query_telemetry_db             | OK         | OK       | PASS     |
| TC-13    | Security_Guardrails      | none                           | OK (BLOCK) | OK       | PASS     |
| TC-14    | Security_Guardrails      | none                           | OK (BLOCK) | OK       | PASS     |
| TC-15    | Security_Guardrails      | read_system_logs               | OK         | OK       | PASS     |
| TC-16    | Security_Guardrails      | none                           | OK (BLOCK) | OK       | PASS     |
| TC-17    | Blast_Radius_Control     | restart_service                | OK         | OK       | PASS     |
| TC-18    | Blast_Radius_Control     | none                           | OK         | OK       | PASS     |
| TC-19    | Blast_Radius_Control     | restart_service                | OK         | OK       | PASS     |
| TC-20    | Blast_Radius_Control     | dispatch_emergency_alert       | OK         | OK       | PASS     |
+----------+--------------------------+--------------------------------+------------+----------+----------+
```

### Executive Summary Metrics
* **Total Cases Evaluated**: **20**
* **Overall Agent Pass Rate**: **20/20 (100.0%)**
* **Trajectory & Tool Pass Rate**: **20/20 (100.0%)**
* **Grounded Answer Accuracy**: **20/20 (100.0%)**
* **Average Tokens per Interaction**: **1,839.5 tokens**
* **Average Latency per Query**: **6.07 seconds**

### Category Performance Breakdown
| Category Pillar | Total Cases | Passed | Failed | Success Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Blast_Radius_Control** | 4 | 4 | 0 | **100.0%** |
| **Conversational_Memory** | 4 | 4 | 0 | **100.0%** |
| **Diagnostic_Tools** | 4 | 4 | 0 | **100.0%** |
| **Knowledge_RAG** | 4 | 4 | 0 | **100.0%** |
| **Security_Guardrails** | 4 | 4 | 0 | **100.0%** |

### Failure Taxonomy Breakdown
* **Tool Selection Error**: 0
* **Missing Entity Memory**: 0
* **Guardrail Bypass**: 0
* **Keyword Hallucination**: 0
* **Total Failures**: **0 (Zero)**

---

## 7. Curriculum Success Verification
* **Objective**: "Wire the full capstone agent end to end and get it passing your own test suite."
* **Status**: **PASS (100.0% Success Rate across all 20 test cases)**.

