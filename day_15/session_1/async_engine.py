"""
Async Agent Execution Engine for OpsSentinel Enterprise.
Orchestrates parallel diagnostic tool dispatch, durable state checkpointing,
human-in-the-loop gating, and runbook RAG synthesis.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

import sys
from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
for _p in [str(_workspace_root), str(_script_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from day_15.session_1.config import config
    from day_15.session_1.query_router import QueryRouter, AdvancedRunbookRetriever, RouteCategory, RoutingDecision
    from day_15.session_1.tools import SREToolRegistry, ToolBlastRadiusTier, ToolExecutionResult
    from day_15.session_1.durable_state import DurableStateCheckpointer, WorkflowStatus, SessionState
    from day_15.session_1.hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalStatus
except ImportError:
    try:
        from .config import config
        from .query_router import QueryRouter, AdvancedRunbookRetriever, RouteCategory, RoutingDecision
        from .tools import SREToolRegistry, ToolBlastRadiusTier, ToolExecutionResult
        from .durable_state import DurableStateCheckpointer, WorkflowStatus, SessionState
        from .hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalStatus
    except ImportError:
        from config import config
        from query_router import QueryRouter, AdvancedRunbookRetriever, RouteCategory, RoutingDecision
        from tools import SREToolRegistry, ToolBlastRadiusTier, ToolExecutionResult
        from durable_state import DurableStateCheckpointer, WorkflowStatus, SessionState
        from hitl_gateway import HITLApprovalGateway, AuditTrailLogger, ApprovalStatus

class AgentExecutionResponse(BaseModel):
    session_id: str
    status: WorkflowStatus
    query: str
    routing_category: str
    target_service: Optional[str] = None
    final_output: str
    latency_ms: float
    total_tokens: int
    estimated_cost: float
    tools_executed: List[str] = Field(default_factory=list)
    pending_approval: Optional[Dict[str, Any]] = None
    checkpoints_count: int = 0

class AsyncAgentEngine:
    """Enterprise-hardened async SRE agent orchestrator."""

    def __init__(
        self,
        checkpointer: Optional[DurableStateCheckpointer] = None,
        approval_gateway: Optional[HITLApprovalGateway] = None,
        audit_logger: Optional[AuditTrailLogger] = None,
    ):
        self.checkpointer = checkpointer or DurableStateCheckpointer()
        self.audit_logger = audit_logger or AuditTrailLogger()
        self.approval_gateway = approval_gateway or HITLApprovalGateway(self.audit_logger)
        self.router = QueryRouter()
        self.retriever = AdvancedRunbookRetriever()
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tools)

    async def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: str = "sre-operator",
        tenant_id: str = "tenant-default"
    ) -> AgentExecutionResponse:
        start_time = time.perf_counter()
        session_id = session_id or f"SES-{uuid.uuid4().hex[:8].upper()}"

        # 1. Initialize Durable Session in SQLite
        session_state = self.checkpointer.create_session(
            session_id=session_id,
            query=query,
            user_id=user_id,
            tenant_id=tenant_id
        )

        # 2. Query Routing & Guardrail Triage
        routing: RoutingDecision = self.router.route_query(query)
        self.checkpointer.update_session(
            session_id=session_id,
            status=WorkflowStatus.ROUTING,
            current_step=1,
            routing_decision=routing.model_dump()
        )
        self.checkpointer.save_checkpoint(session_id, "QUERY_ROUTED", {
            "current_step": 1,
            "routing": routing.model_dump()
        })

        tokens_consumed = 80 + len(query.split()) * 2
        tools_run: List[str] = []

        # -------------------------------------------------------------
        # BRANCH A: ADVERSARIAL ATTACK (Blocked at Layer 0)
        # -------------------------------------------------------------
        if routing.is_blocked:
            self.audit_logger.log_event(
                event_type="GUARDRAIL_INTERCEPTION",
                session_id=session_id,
                operator_id=user_id,
                details={"query": query, "rationale": routing.rationale}
            )
            blocked_msg = f"SECURITY ALERT: Request blocked by Layer 0 Guardrail. Reason: {routing.rationale}"
            self.checkpointer.update_session(
                session_id=session_id,
                status=WorkflowStatus.ABORTED,
                current_step=2,
                final_output=blocked_msg
            )
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return AgentExecutionResponse(
                session_id=session_id,
                status=WorkflowStatus.ABORTED,
                query=query,
                routing_category=routing.category,
                target_service=routing.target_service,
                final_output=blocked_msg,
                latency_ms=round(elapsed, 2),
                total_tokens=tokens_consumed,
                estimated_cost=round((tokens_consumed / 1000.0) * config.input_cost_per_1k, 6),
                tools_executed=[],
                checkpoints_count=2
            )

        # -------------------------------------------------------------
        # BRANCH B: INFORMATIONAL SOP / RUNBOOK RAG
        # -------------------------------------------------------------
        if routing.category == RouteCategory.INFO_SOP:
            results = self.retriever.search(query, service_filter=routing.target_service, top_k=2)
            if results:
                top_rb, score = results[0]
                output_msg = (
                    f"### Standard Operating Procedure: {top_rb.title} ({top_rb.runbook_id})\n"
                    f"**Service:** `{top_rb.service}` | **Severity:** `{top_rb.severity}` | **Relevance Score:** {score:.2f}\n\n"
                    f"**Context:** {top_rb.content}\n\n"
                    f"**Recommended Remediation Steps:**\n" +
                    "\n".join(f"{i+1}. {step}" for i, step in enumerate(top_rb.remediation_steps))
                )
            else:
                output_msg = f"No specific runbook found matching '{query}'. Please consult the central SRE wiki or on-call lead."

            tokens_consumed += 210
            self.checkpointer.update_session(
                session_id=session_id,
                status=WorkflowStatus.COMPLETED,
                current_step=2,
                final_output=output_msg
            )
            self.checkpointer.save_checkpoint(session_id, "SOP_RETRIEVAL_COMPLETED", {
                "current_step": 2,
                "matches": len(results)
            })
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return AgentExecutionResponse(
                session_id=session_id,
                status=WorkflowStatus.COMPLETED,
                query=query,
                routing_category=routing.category,
                target_service=routing.target_service,
                final_output=output_msg,
                latency_ms=round(elapsed, 2),
                total_tokens=tokens_consumed,
                estimated_cost=round((tokens_consumed / 1000.0) * config.input_cost_per_1k, 6),
                tools_executed=[],
                checkpoints_count=len(self.checkpointer.get_checkpoints(session_id))
            )

        # -------------------------------------------------------------
        # BRANCH C: DESTRUCTIVE WRITE (Requires Human Approval Gate)
        # -------------------------------------------------------------
        if routing.requires_hitl and routing.action_type:
            action = routing.action_type
            svc = routing.target_service or "unknown-service"

            # Create approval request
            blast_radius = f"Will execute Tier 3 destructive command '{action}' on target service '{svc}'."
            compensating = {"action": f"rollback_{action}", "target_service": svc}
            approval_req = self.approval_gateway.request_approval(
                session_id=session_id,
                tool_name=action,
                input_params={"service_name": svc},
                blast_radius_summary=blast_radius,
                compensating_action=compensating
            )

            approval_notice = (
                f"### ACTION SUSPENDED: Human SRE Approval Required (Tier 3 Gate)\n"
                f"- **Approval ID:** `{approval_req.approval_id}`\n"
                f"- **Target Service:** `{svc}`\n"
                f"- **Requested Tool:** `{action}`\n"
                f"- **Blast Radius:** {blast_radius}\n"
                f"- **State:** Execution checkpointed to SQLite. Send `POST /api/v1/hitl/approve` with Approval ID to execute."
            )

            self.checkpointer.update_session(
                session_id=session_id,
                status=WorkflowStatus.AWAITING_APPROVAL,
                current_step=2,
                pending_approval_id=approval_req.approval_id,
                final_output=approval_notice
            )
            self.checkpointer.save_checkpoint(session_id, "AWAITING_HUMAN_APPROVAL", {
                "current_step": 2,
                "approval_id": approval_req.approval_id,
                "tool": action
            })

            elapsed = (time.perf_counter() - start_time) * 1000.0
            return AgentExecutionResponse(
                session_id=session_id,
                status=WorkflowStatus.AWAITING_APPROVAL,
                query=query,
                routing_category=routing.category,
                target_service=svc,
                final_output=approval_notice,
                latency_ms=round(elapsed, 2),
                total_tokens=tokens_consumed,
                estimated_cost=round((tokens_consumed / 1000.0) * config.input_cost_per_1k, 6),
                tools_executed=[],
                pending_approval=approval_req.model_dump(),
                checkpoints_count=len(self.checkpointer.get_checkpoints(session_id))
            )

        # -------------------------------------------------------------
        # BRANCH D: DIAGNOSTIC READ (Parallel Tool Dispatch via asyncio.gather)
        # -------------------------------------------------------------
        svc = routing.target_service or "auth-service"
        self.checkpointer.update_session(
            session_id=session_id,
            status=WorkflowStatus.DIAGNOSING,
            current_step=2
        )

        async with self.semaphore:
            # Parallel execution of 4 diagnostic read tools
            t1 = SREToolRegistry.fetch_service_metrics(svc)
            t2 = SREToolRegistry.fetch_cluster_logs(svc)
            t3 = SREToolRegistry.check_endpoint_health(svc)
            t4 = SREToolRegistry.get_service_topology(svc)

            results: List[ToolExecutionResult] = await asyncio.gather(t1, t2, t3, t4)

        # Record each execution in SQLite
        for idx, res in enumerate(results):
            tools_run.append(res.tool_name)
            self.checkpointer.record_tool_execution(
                execution_id=f"EX-{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                step_index=2,
                tool_name=res.tool_name,
                tier=res.tier.value,
                input_params={"service": svc},
                output_result=res.output,
                status=res.status,
                latency_ms=res.latency_ms
            )

        self.checkpointer.save_checkpoint(session_id, "PARALLEL_DIAGNOSTICS_EXECUTED", {
            "current_step": 2,
            "tools_count": len(results),
            "service": svc
        })

        # Synthesize diagnostic report
        metrics_data = results[0].output.get("metrics", {})
        logs_data = results[1].output.get("log_entries", [])
        health_data = results[2].output.get("health_summary", {})
        topology_data = results[3].output.get("topology", {})

        diagnostic_synthesis = (
            f"### Comprehensive Infrastructure Diagnostic: `{svc}`\n"
            f"**Endpoint Status:** `{health_data.get('status', 'UNKNOWN')}` (HTTP {health_data.get('http_code')}) | "
            f"**Cluster Topology:** `{topology_data.get('cluster')}` ({topology_data.get('replicas')} Replicas)\n\n"
            f"#### Key Telemetry Metrics:\n"
            f"- **CPU Utilization:** {metrics_data.get('cpu_percent')}% | **Memory:** {metrics_data.get('memory_mb')} MB\n"
            f"- **p95 Latency:** {metrics_data.get('p95_latency_ms', 'N/A')} ms | **Error Rate:** {metrics_data.get('error_rate_pct', 'N/A')}%\n\n"
            f"#### Topology & Upstream/Downstream Dependencies:\n"
            f"- **Cluster Topology:** `{topology_data.get('cluster')}` | **Replicas:** {topology_data.get('replicas')}\n"
            f"- **Dependencies:** {', '.join(topology_data.get('dependencies', [])) or 'None'}\n\n"
            f"#### Recent Log Anomalies:\n" +
            "\n".join(f"- `{log}`" for log in logs_data[:3]) + "\n\n"
            f"**Root Cause Assessment:** High resource pressure and downstream timeouts detected. "
            f"Consider clearing Redis cache or executing rolling restart if degraded."
        )

        tokens_consumed += 340
        self.checkpointer.update_session(
            session_id=session_id,
            status=WorkflowStatus.COMPLETED,
            current_step=3,
            final_output=diagnostic_synthesis
        )
        self.checkpointer.save_checkpoint(session_id, "DIAGNOSTIC_COMPLETED", {
            "current_step": 3,
            "status": "SUCCESS"
        })

        elapsed = (time.perf_counter() - start_time) * 1000.0
        return AgentExecutionResponse(
            session_id=session_id,
            status=WorkflowStatus.COMPLETED,
            query=query,
            routing_category=routing.category,
            target_service=svc,
            final_output=diagnostic_synthesis,
            latency_ms=round(elapsed, 2),
            total_tokens=tokens_consumed,
            estimated_cost=round((tokens_consumed / 1000.0) * config.input_cost_per_1k, 6),
            tools_executed=tools_run,
            checkpoints_count=len(self.checkpointer.get_checkpoints(session_id))
        )

    async def resume_after_approval(
        self,
        session_id: str,
        approval_id: str,
        operator_id: str
    ) -> AgentExecutionResponse:
        """Resumes a suspended workflow after human approval is confirmed."""
        start_time = time.perf_counter()
        session_state = self.checkpointer.get_session(session_id)
        if not session_state:
            raise ValueError(f"Session '{session_id}' not found.")

        approval_req = self.approval_gateway.get_approval(approval_id)
        if not approval_req:
            raise ValueError(f"Approval '{approval_id}' not found.")
        if approval_req.status != ApprovalStatus.APPROVED:
            raise ValueError(f"Approval '{approval_id}' is not in APPROVED state (current: {approval_req.status.value}).")

        tool_name = approval_req.tool_name
        params = approval_req.input_params
        svc = params.get("service_name", "unknown-service")

        self.checkpointer.update_session(
            session_id=session_id,
            status=WorkflowStatus.EXECUTING_ACTION,
            current_step=3
        )

        # Execute approved Tier 3 tool
        if tool_name == "restart_service":
            res = await SREToolRegistry.restart_service(svc)
        elif tool_name == "rollback_deployment":
            res = await SREToolRegistry.rollback_deployment(svc)
        elif tool_name == "scale_deployment":
            res = await SREToolRegistry.scale_deployment(svc, params.get("replicas", 6))
        elif tool_name == "drop_stale_connections":
            res = await SREToolRegistry.drop_stale_connections(svc)
        else:
            raise ValueError(f"Unknown remediation tool '{tool_name}'")

        # Record in SQLite & Audit Log
        self.checkpointer.record_tool_execution(
            execution_id=f"EX-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            step_index=3,
            tool_name=tool_name,
            tier=res.tier.value,
            input_params=params,
            output_result=res.output,
            status=res.status,
            latency_ms=res.latency_ms
        )

        self.audit_logger.log_event(
            event_type="REMEDIATION_EXECUTED",
            session_id=session_id,
            operator_id=operator_id,
            details={
                "tool_name": tool_name,
                "params": params,
                "output": res.output,
                "compensating_action": res.compensating_action
            }
        )

        completion_msg = (
            f"### REMEDIATION COMPLETED: `{tool_name}` on `{svc}`\n"
            f"- **Authorized By:** `{operator_id}`\n"
            f"- **Execution Status:** `{res.status}` ({res.latency_ms} ms)\n"
            f"- **Result Details:** {res.output}\n"
            f"- **Compensating Rollback Registered:** `{res.compensating_action.get('action') if res.compensating_action else 'None'}`"
        )

        self.checkpointer.update_session(
            session_id=session_id,
            status=WorkflowStatus.COMPLETED,
            current_step=4,
            final_output=completion_msg
        )
        self.checkpointer.save_checkpoint(session_id, "REMEDIATION_ACTION_COMPLETED", {
            "current_step": 4,
            "tool": tool_name,
            "status": res.status
        })

        elapsed = (time.perf_counter() - start_time) * 1000.0
        return AgentExecutionResponse(
            session_id=session_id,
            status=WorkflowStatus.COMPLETED,
            query=session_state["query"],
            routing_category=RouteCategory.DESTRUCTIVE_WRITE,
            target_service=svc,
            final_output=completion_msg,
            latency_ms=round(elapsed, 2),
            total_tokens=150,
            estimated_cost=round((150 / 1000.0) * config.input_cost_per_1k, 6),
            tools_executed=[tool_name],
            checkpoints_count=len(self.checkpointer.get_checkpoints(session_id))
        )
