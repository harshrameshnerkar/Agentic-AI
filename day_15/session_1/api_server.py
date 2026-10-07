"""
FastAPI Production Microservice for OpsSentinel Enterprise (Day 15).
Provides REST endpoints for agent execution, durable session inspection,
human-in-the-loop approvals, audit verification, and Prometheus/JSON metrics.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import time
import sys
from pathlib import Path

# Enable both direct script execution and package imports
_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
for _p in [str(_workspace_root), str(_script_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from day_15.session_1.config import config
    from day_15.session_1.async_engine import AsyncAgentEngine, AgentExecutionResponse
    from day_15.session_1.durable_state import DurableStateCheckpointer, WorkflowStatus
    from day_15.session_1.hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalRequest
except ImportError:
    try:
        from .config import config
        from .async_engine import AsyncAgentEngine, AgentExecutionResponse
        from .durable_state import DurableStateCheckpointer, WorkflowStatus
        from .hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalRequest
    except ImportError:
        from config import config
        from async_engine import AsyncAgentEngine, AgentExecutionResponse
        from durable_state import DurableStateCheckpointer, WorkflowStatus
        from hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalRequest

# Initialize Singletons
checkpointer = DurableStateCheckpointer()
audit_logger = AuditTrailLogger()
approval_gateway = HITLApprovalGateway(audit_logger)
engine = AsyncAgentEngine(checkpointer, approval_gateway, audit_logger)

app = FastAPI(
    title="OpsSentinel Enterprise Agent API",
    description="Hardened Autonomous SRE Copilot with Async Execution, Checkpointing, and HITL Gating.",
    version=config.version
)

# -------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------

class RunAgentRequest(BaseModel):
    query: str = Field(..., example="Inspect high CPU and 500 error rate on auth-service")
    session_id: Optional[str] = None
    user_id: str = "sre-oncall"
    tenant_id: str = "tenant-default"

class ApprovalDecisionRequest(BaseModel):
    approval_id: str = Field(..., example="APV-A1B2C3D4")
    operator_id: str = Field(..., example="sre-senior-engineer")
    rationale: str = Field("Authorized remediation for P1 incident", example="Approved after verifying replica status")

class ResumeSessionRequest(BaseModel):
    approval_id: str
    operator_id: str = "sre-senior-engineer"

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "HEALTHY",
        "service": config.service_name,
        "environment": config.environment,
        "version": config.version,
        "audit_chain_intact": audit_logger.verify_integrity()
    }

@app.post("/api/v1/agent/run", response_model=AgentExecutionResponse, tags=["Agent Execution"])
async def run_agent(req: RunAgentRequest):
    try:
        response = await engine.run(
            query=req.query,
            session_id=req.session_id,
            user_id=req.user_id,
            tenant_id=req.tenant_id
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {str(e)}"
        )

@app.get("/api/v1/agent/sessions", tags=["Session State"])
async def list_sessions(limit: int = 30):
    return checkpointer.list_active_sessions(limit=limit)

@app.get("/api/v1/agent/sessions/{session_id}", tags=["Session State"])
async def get_session_details(session_id: str):
    sess = checkpointer.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    checkpoints = checkpointer.get_checkpoints(session_id)
    return {
        "session": sess,
        "checkpoints": checkpoints,
        "checkpoints_count": len(checkpoints)
    }

@app.post("/api/v1/agent/sessions/{session_id}/resume", response_model=AgentExecutionResponse, tags=["Agent Execution"])
async def resume_session(session_id: str, req: ResumeSessionRequest):
    try:
        response = await engine.resume_after_approval(
            session_id=session_id,
            approval_id=req.approval_id,
            operator_id=req.operator_id
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")

@app.get("/api/v1/hitl/pending", tags=["Human-in-the-Loop"])
async def list_pending_approvals():
    return approval_gateway.get_pending_approvals()

@app.post("/api/v1/hitl/approve", tags=["Human-in-the-Loop"])
async def approve_request(req: ApprovalDecisionRequest):
    try:
        result = approval_gateway.approve(
            approval_id=req.approval_id,
            operator_id=req.operator_id,
            rationale=req.rationale
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.post("/api/v1/hitl/reject", tags=["Human-in-the-Loop"])
async def reject_request(req: ApprovalDecisionRequest):
    try:
        result = approval_gateway.reject(
            approval_id=req.approval_id,
            operator_id=req.operator_id,
            rationale=req.rationale
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.get("/api/v1/audit/integrity", tags=["Security & Audit"])
async def verify_audit_integrity():
    is_valid = audit_logger.verify_integrity()
    return {
        "tamper_evident_integrity": is_valid,
        "chain_algorithm": "SHA-256 forward hash-chain",
        "log_path": str(config.audit_log_path)
    }

@app.get("/api/v1/telemetry", tags=["Observability"])
async def get_telemetry():
    sessions = checkpointer.list_active_sessions(limit=100)
    total = len(sessions)
    completed = sum(1 for s in sessions if s["status"] == "COMPLETED")
    pending = sum(1 for s in sessions if s["status"] == "AWAITING_APPROVAL")
    aborted = sum(1 for s in sessions if s["status"] == "ABORTED")

    pass_rate = (completed / total * 100.0) if total > 0 else 100.0
    return {
        "service": config.service_name,
        "total_sessions": total,
        "completed_count": completed,
        "pending_approval_count": pending,
        "aborted_guardrail_count": aborted,
        "pass_rate_pct": round(pass_rate, 2),
        "target_p95_latency_ms": config.max_ci_p95_latency_ms,
        "environment": config.environment
    }

if __name__ == "__main__":
    uvicorn.run(app, host=config.api_host, port=config.api_port)
