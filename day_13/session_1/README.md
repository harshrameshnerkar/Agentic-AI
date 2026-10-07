# Day 13 - Session 1: Async & Concurrency

Welcome to **Session 1** of **Day 13** in the **Agentic AI Engineering Curriculum**.

This session transitions the Capstone OpsSentinel SRE Copilot from synchronous, blocking tool invocations to a production-grade **Asynchronous Concurrent Architecture** with parallel tool calling, worker queues, polling endpoints, webhooks, and graceful cancellation.

---

## 1. Architectural Highlights

### Sequential vs. Parallel Tool Execution
In enterprise SRE incident response, an agent routinely queries multiple independent diagnostic endpoints:
1. **Telemetry Database**: Active connections, error rates, CPU allocation (~120ms I/O)
2. **Container System Logs**: Disk log retrieval from worker nodes (~150ms I/O)
3. **Vector Semantic Search**: Retrieval of matching standard operating runbooks (~180ms I/O)
4. **SLA Arithmetic Engine**: Error rate and budget burn rate computation (~25ms I/O)

```
SEQUENTIAL (BLOCKING) EXECUTION:
[ Telemetry DB (120ms) ] ──> [ System Logs (150ms) ] ──> [ Vector Runbooks (180ms) ] ──> Total: 450ms + Overhead

CONCURRENT (ASYNC GATHER) EXECUTION:
┌── [ Telemetry DB (120ms) ] ──┐
├── [ System Logs (150ms) ] ───┼──> Total: max(120, 150, 180) = ~180ms (60% Latency Cut!)
└── [ Vector Runbooks (180ms) ]┘
```

---

## 2. Empirical Latency Reduction Scorecard

Measured across 5 representative multi-tool Capstone SRE triage scenarios:

| Scenario ID | Incident Workload | Tools | Sequential Latency | Parallel Latency | Latency Reduction | Speedup Factor |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **SCEN-01** | Payment Gateway Latency Spike | 3 | 477.5 ms | 186.9 ms | **-290.6 ms (-60.9%)** | **2.56x** |
| **SCEN-02** | Postgres Connection Saturation | 3 | 486.0 ms | 186.2 ms | **-299.8 ms (-61.7%)** | **2.61x** |
| **SCEN-03** | Nginx Ingress 504 Burst | 3 | 487.6 ms | 187.0 ms | **-300.5 ms (-61.6%)** | **2.61x** |
| **SCEN-04** | Payment SLA Error Calculation | 4 | 523.5 ms | 188.7 ms | **-334.8 ms (-63.9%)** | **2.77x** |
| **SCEN-05** | General Cluster Health Sweep | 4 | 525.7 ms | 192.1 ms | **-333.6 ms (-63.5%)** | **2.74x** |
| **OVERALL** | **Full Benchmark Workload** | **17** | **2,500.2 ms** | **940.8 ms** | **-1,559.4 ms (-62.4%)** | **2.66x Speedup** |

---

## 3. Worker Queues, Polling, and Webhooks

For long-running tasks, synchronous HTTP connections time out. The `AgentWorkerQueue` (`worker_queue.py`) implements:
- **Producer-Consumer Architecture**: Powered by `asyncio.Queue` and a dedicated worker coroutine pool.
- **Job Lifecycle States**: `PENDING` $\to$ `RUNNING` $\to$ `COMPLETED` / `FAILED` / `CANCELLED`.
- **Client Polling Endpoint**: `get_job_status(job_id)` provides real-time elapsed time and stage updates.
- **Webhook Dispatch**: Dispatches signed HTTP callback payloads to subscribers upon terminal state transition.
- **Graceful Cancellation**: `cancel_job(job_id)` halts running tasks, releases resources, and prevents destructive actions from triggering.

---

## 4. How to Run

```powershell
# 1. Run the Sequential vs. Parallel Latency Benchmark
python day_13/session_1/main.py --benchmark

# 2. Run the Worker Queue & Webhook Demonstration
python day_13/session_1/main.py --worker-queue

# 3. Run the Job Cancellation Demonstration
python day_13/session_1/main.py --cancel-demo

# 4. Run an ad-hoc query with parallel tool execution
python day_13/session_1/main.py --query "Postgres connection pool nearing 98% saturation."
```
