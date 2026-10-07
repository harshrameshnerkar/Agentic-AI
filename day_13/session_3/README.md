# Day 13 - Session 3: Deployment & Scaling

Welcome to **Session 3** of **Day 13** in the **Agentic AI Engineering Curriculum**.

This session operationalizes the Capstone OpsSentinel SRE Agent for production cloud deployment, implementing **secure multi-stage containerization**, **secret masking**, **stateless horizontal scaling**, **cross-replica distributed rate limiting**, and an **automated multi-provider failover path with graceful safe-mode degradation**.

---

## 1. Containerization & Secret Management

### Production Multi-Stage Dockerfile (`Dockerfile`)
- **Stage 1 (Builder)**: Compiles C extensions and wheels in an isolated builder container.
- **Stage 2 (Runtime)**: Copies only compiled artifacts into `python:3.12-slim`.
- **Non-Root Execution**: Runs under unprivileged user `appuser` (UID `10001`, GID `10001`).
- **Zero Baked Secrets**: Credentials are never placed into image layers or build args. Injected dynamically via environment variables / Kubernetes Secrets.
- **Built-in Healthcheck**: Docker and Kubernetes poll `GET /health` every 30s.

### Environment & Secret Masking (`config.py`)
All credentials are encapsulated in `MaskedSecret`. String representations and logs automatically redact secrets:
```python
anthropic_api_key = MaskedSecret("sk-ant-live-9482710491823749")
print(anthropic_api_key)  # Emits: 'sk-a****3749'
```

---

## 2. Multi-Provider Failover & Circuit Breakers (`provider_failover.py`)

Frontier model APIs experience rate limits, latency spikes, and 503 outages. OpsSentinel implements an automatic 4-tier failover cascade:

```
                  ┌────────────────────────────────────────┐
                  │       Incoming Incident Request        │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Tier 1: Anthropic       │
                        │  (Claude 3.5 Sonnet)      │
                        └─────────────┬─────────────┘
                                      │ (503 / 429 / Timeout)
                                      ▼
                        ┌───────────────────────────┐
                        │   Tier 2: OpenAI          │
                        │      (GPT-4o)             │
                        └─────────────┬─────────────┘
                                      │ (Outage Cascade)
                                      ▼
                        ┌───────────────────────────┐
                        │   Tier 3: Google Gemini   │
                        │     (Gemini 1.5 Pro)      │
                        └─────────────┬─────────────┘
                                      │ (Complete Cloud Outage)
                                      ▼
                        ┌───────────────────────────┐
                        │   Tier 4: Local SLM       │
                        │ (Safe-Mode Degradation)   │
                        └───────────────────────────┘
```

### Circuit Breaker States
- **CLOSED**: Healthy. All traffic routes to provider.
- **OPEN**: Error threshold exceeded ($\ge 3$ consecutive errors). Traffic automatically bypasses the provider for 15 seconds to prevent latency build-up.
- **HALF_OPEN**: Cooldown period elapsed. A probe query is sent to test recovery. If successful, circuit transitions back to CLOSED.

---

## 3. Distributed Rate Limiting & Backoff (`distributed_rate_limiter.py`)

When running multiple stateless replicas behind a load balancer, independent in-memory rate limiters cause aggregated quota violations. OpsSentinel implements:
- **Shared Token Bucket**: Atomic token replenishment across all worker nodes.
- **Exponential Backoff with Full Jitter**:
  $$t_{\text{sleep}} = \text{Uniform}\left(0.01, \min\left(t_{\text{max}}, t_{\text{base}} \times 2^{\text{attempt}}\right)\right)$$
  Prevents the **thundering herd problem** when recovering from upstream 429 penalties.

---

## 4. How to Run & Verify

```powershell
# 1. Run the Multi-Tier Failover and Rate Limiter Simulation
python day_13/session_3/main.py

# 2. Test Only the Multi-Provider Circuit Breaker Failover Path
python day_13/session_3/main.py --simulate-failover

# 3. Test Distributed Token Bucket with 8 Concurrent Requests
python day_13/session_3/main.py --test-rate-limiter

# 4. Verify Secret Masking & Configuration
python day_13/session_3/main.py --check-config

# 5. Launch the Local FastAPI Server
python day_13/session_3/main.py --serve
```
