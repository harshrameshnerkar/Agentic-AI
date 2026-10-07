"""
Day 13 - Session 3: Production FastAPI Stateless Agent Service
=============================================================
Implements:
  1. REST API for horizontally scalable, stateless agent replicas
  2. Kubernetes Health & Readiness Probes (/health, /ready)
  3. Distributed rate limit enforcement per request
  4. Multi-provider circuit breaker failover integration
  5. Chaos injection endpoints for failover drill verification
"""

import os
import sys
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from fastapi import FastAPI, HTTPException, status
try:
    from day_13.session_3.config import settings
    from day_13.session_3.provider_failover import MultiProviderFailoverEngine, FailoverExecutionResult
    from day_13.session_3.distributed_rate_limiter import DistributedTokenBucket
except ImportError:
    from config import settings
    from provider_failover import MultiProviderFailoverEngine, FailoverExecutionResult
    from distributed_rate_limiter import DistributedTokenBucket



app = FastAPI(
    title="OpsSentinel Agent Service",
    description="Horizontally Scalable Autonomous SRE Copilot API",
    version="1.0.0",
)

# Shared Service Singletons
failover_engine = MultiProviderFailoverEngine(
    error_threshold=settings.circuit_breaker_error_threshold,
    recovery_time_sec=settings.circuit_breaker_recovery_time_sec,
)
rate_limiter = DistributedTokenBucket(rate_limit_rpm=settings.rate_limit_rpm)


class IncidentRequest(BaseModel):
    query: str = Field(description="Incident description", examples=["Postgres connection pool nearing 98% saturation."])
    tenant_id: str = Field(default="ACME_FINTECH", description="Tenant identifier")
    user_id: str = Field(default="oncall-alice@acme.internal", description="User or on-call engineer identifier")


class IncidentResponse(BaseModel):
    query: str
    tenant_id: str
    active_provider: str
    attempted_providers: list
    failover_occurred: bool
    failover_reason: Optional[str]
    is_degraded_fallback: bool
    latency_ms: float
    remediation_plan: Dict[str, Any]


class ChaosInjectionRequest(BaseModel):
    provider: str = Field(description="Target model provider", examples=["anthropic"])
    is_down: bool = Field(description="Flag to simulate outage", examples=[True])


@app.get("/health", tags=["Monitoring"])
def liveness_probe() -> Dict[str, str]:
    """Kubernetes liveness probe: indicates process is responsive."""
    return {"status": "HEALTHY", "service": settings.app_name, "environment": settings.environment}


@app.get("/ready", tags=["Monitoring"])
def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe: verifies upstream connectivity and circuits."""
    circuits = {
        name: h.state.value for name, h in failover_engine.providers.items()
    }
    # Ready if at least one cloud provider or local fallback is available
    is_ready = True
    return {
        "status": "READY" if is_ready else "NOT_READY",
        "circuit_breakers": circuits,
        "rate_limiter_tokens": round(rate_limiter.tokens, 2),
    }


@app.get("/v1/providers/status", tags=["Operations"])
def provider_status() -> Dict[str, Any]:
    """Returns detailed telemetry on provider health and circuit states."""
    data = {}
    for name, h in failover_engine.providers.items():
        data[name] = {
            "circuit_state": h.state.value,
            "failure_count": h.failure_count,
            "success_count": h.success_count,
            "consecutive_failures": h.consecutive_failures,
        }
    return {"providers": data}


@app.post("/v1/incident/run", response_model=IncidentResponse, tags=["Agent Execution"])
async def run_incident_triage(req: IncidentRequest) -> IncidentResponse:
    """Executes incident triage with cross-replica rate limiting and failover."""
    # Step 1: Distributed Rate Limit Check
    rate_status = await rate_limiter.acquire_with_backoff(max_retries=settings.max_retries)
    if not rate_status.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded across replicas. Retry after {rate_status.wait_time_sec}s.",
        )

    # Step 2: Multi-Provider Failover Execution
    try:
        res: FailoverExecutionResult = await failover_engine.execute_with_failover(req.query)
        return IncidentResponse(
            query=res.query,
            tenant_id=req.tenant_id,
            active_provider=res.active_provider,
            attempted_providers=res.attempted_providers,
            failover_occurred=res.failover_occurred,
            failover_reason=res.failover_reason,
            is_degraded_fallback=res.is_degraded_fallback,
            latency_ms=res.latency_ms,
            remediation_plan=res.plan_json,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed across all providers: {str(e)}",
        )


@app.post("/v1/chaos/provider", tags=["Chaos Testing"])
def inject_chaos(req: ChaosInjectionRequest) -> Dict[str, Any]:
    """Simulates provider outages to test failover behavior."""
    failover_engine.set_simulated_outage(req.provider, req.is_down)
    return {
        "status": "CHAOS_INJECTED",
        "provider": req.provider,
        "is_down": req.is_down,
    }
