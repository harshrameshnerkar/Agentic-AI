"""
Day 13 - Session 1: Async Capstone Agent with Parallel Tool Calling
===================================================================
Implements:
  1. Asynchronous Agent Engine (Async API invocations, non-blocking coroutines)
  2. Parallel Tool Execution via asyncio.gather (independent diagnostic queries)
  3. Timeouts & Cancellation (asyncio.wait_for, asyncio.CancelledError cleanup)
  4. Dual Execution Modes:
       - mode="sequential": Synchronous baseline (for rigorous latency comparison)
       - mode="parallel": Asynchronous concurrent tool execution
  5. Detailed execution telemetry (wall-clock latency, tool-level timings)
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from async_tools import (
    sync_query_telemetry_db,
    sync_read_system_logs,
    sync_search_runbooks,
    sync_calculate_metrics,
    sync_restart_service,
    async_query_telemetry_db,
    async_read_system_logs,
    async_search_runbooks,
    async_calculate_metrics,
    async_restart_service,
    async_rollback_deployment,
    async_dispatch_emergency_alert,
)


@dataclass
class ToolCallSpec:
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class AgentRunResult:
    query: str
    mode: str                    # "sequential" | "parallel"
    tools_called: List[str]
    tool_results: List[Dict[str, Any]]
    final_action_plan: Dict[str, Any]
    wall_clock_latency_ms: float
    total_tool_latency_sum_ms: float
    concurrency_efficiency_pct: float
    timed_out: bool = False
    cancelled: bool = False


class AsyncCapstoneAgent:
    """
    Autonomous Enterprise SRE Copilot with Concurrent Tool Orchestration.
    Executes multiple independent diagnostic tools (Telemetry DB, Container Logs, Runbooks)
    in parallel using asyncio.gather to achieve maximum throughput and minimal MTTR.
    """

    def __init__(
        self,
        default_tool_timeout_sec: float = 2.0,
        global_run_timeout_sec: float = 5.0,
    ):
        self.default_tool_timeout = default_tool_timeout_sec
        self.global_run_timeout = global_run_timeout_sec

    def plan_tools_for_query(self, query: str) -> List[ToolCallSpec]:
        """
        Decomposes an incident query into independent diagnostic tool calls.
        For enterprise SRE triage, queries typically require:
          1. Checking telemetry database (CPU, error rate, connections)
          2. Inspecting container system logs
          3. Searching corporate vector runbooks
        """
        q = query.lower()
        tools: List[ToolCallSpec] = []

        if "payment" in q:
            tools.append(ToolCallSpec("query_telemetry_db", {"table": "services", "filter_service": "payment-api"}))
            tools.append(ToolCallSpec("read_system_logs", {"path": "/var/log/payment-api.log", "max_lines": 5}))
            tools.append(ToolCallSpec("search_runbooks", {"query": "Payment API Gateway Timeout & Latency Spike"}))
        elif "postgres" in q or "database" in q:
            tools.append(ToolCallSpec("query_telemetry_db", {"table": "services", "filter_service": "postgres-primary"}))
            tools.append(ToolCallSpec("read_system_logs", {"path": "/var/log/postgres.log", "max_lines": 5}))
            tools.append(ToolCallSpec("search_runbooks", {"query": "Postgres Connection Pool Exhaustion"}))
        elif "ingress" in q or "nginx" in q or "504" in q:
            tools.append(ToolCallSpec("query_telemetry_db", {"table": "services", "filter_service": "nginx-ingress"}))
            tools.append(ToolCallSpec("read_system_logs", {"path": "/var/log/nginx-ingress.log", "max_lines": 5}))
            tools.append(ToolCallSpec("search_runbooks", {"query": "Nginx Ingress 504 Gateway Timeout Investigation"}))
        else:
            # Default tri-tool diagnostic inspection
            tools.append(ToolCallSpec("query_telemetry_db", {"table": "services"}))
            tools.append(ToolCallSpec("read_system_logs", {"path": "/var/log/payment-api.log", "max_lines": 3}))
            tools.append(ToolCallSpec("search_runbooks", {"query": "General Service Incident Triage"}))

        # Optional SLA calculation if metrics/percent are mentioned
        if any(w in q for w in ["calculate", "sla", "error rate", "ratio", "percent"]):
            tools.append(ToolCallSpec("calculate_metrics", {"expression": "100 - (4.2 * 10)"}))

        return tools

    def _execute_tool_sync(self, spec: ToolCallSpec) -> Dict[str, Any]:
        """Executes a single tool synchronously."""
        name = spec.tool_name
        args = spec.arguments
        if name == "query_telemetry_db":
            return sync_query_telemetry_db(args.get("table", "services"), args.get("filter_service"))
        elif name == "read_system_logs":
            return sync_read_system_logs(args.get("path", ""), args.get("max_lines", 5))
        elif name == "search_runbooks":
            return sync_search_runbooks(args.get("query", ""))
        elif name == "calculate_metrics":
            return sync_calculate_metrics(args.get("expression", "100 - 1"))
        elif name == "restart_service":
            return sync_restart_service(args.get("service", ""), args.get("approval_token", ""))
        return {"status": "ERROR", "error": f"Unknown tool '{name}'", "latency_ms": 0.0}

    async def _execute_tool_async(self, spec: ToolCallSpec) -> Dict[str, Any]:
        """Executes a single tool asynchronously with per-tool timeout."""
        name = spec.tool_name
        args = spec.arguments

        async def _call() -> Dict[str, Any]:
            if name == "query_telemetry_db":
                return await async_query_telemetry_db(args.get("table", "services"), args.get("filter_service"))
            elif name == "read_system_logs":
                return await async_read_system_logs(args.get("path", ""), args.get("max_lines", 5))
            elif name == "search_runbooks":
                return await async_search_runbooks(args.get("query", ""))
            elif name == "calculate_metrics":
                return await async_calculate_metrics(args.get("expression", "100 - 1"))
            elif name == "restart_service":
                return await async_restart_service(args.get("service", ""), args.get("approval_token", ""))
            elif name == "rollback_deployment":
                return await async_rollback_deployment(args.get("service", ""), args.get("target_version", ""), args.get("approval_token", ""))
            elif name == "dispatch_emergency_alert":
                return await async_dispatch_emergency_alert(args.get("channel", ""), args.get("message", ""))
            return {"status": "ERROR", "error": f"Unknown tool '{name}'", "latency_ms": 0.0}

        try:
            return await asyncio.wait_for(_call(), timeout=self.default_tool_timeout)
        except asyncio.TimeoutError:
            return {"status": "TIMEOUT", "tool": name, "error": f"Tool '{name}' timed out after {self.default_tool_timeout}s", "latency_ms": self.default_tool_timeout * 1000}
        except asyncio.CancelledError:
            raise

    def run_sequential(self, query: str) -> AgentRunResult:
        """
        Synchronous baseline: Executes tool calls strictly one after another in series.
        Total tool latency = sum(tool_1, tool_2, ..., tool_N).
        """
        t0 = time.perf_counter()
        specs = self.plan_tools_for_query(query)
        results: List[Dict[str, Any]] = []

        for spec in specs:
            res = self._execute_tool_sync(spec)
            results.append(res)

        wall_clock_ms = (time.perf_counter() - t0) * 1000.0
        total_sum_ms = sum(r.get("latency_ms", 0.0) for r in results)

        action_plan = self._formulate_action_plan(query, results)

        return AgentRunResult(
            query=query,
            mode="sequential",
            tools_called=[s.tool_name for s in specs],
            tool_results=results,
            final_action_plan=action_plan,
            wall_clock_latency_ms=round(wall_clock_ms, 2),
            total_tool_latency_sum_ms=round(total_sum_ms, 2),
            concurrency_efficiency_pct=0.0,
        )

    async def run_parallel(self, query: str) -> AgentRunResult:
        """
        Asynchronous Capstone: Dispatches independent tool calls simultaneously via asyncio.gather.
        Total tool latency = max(tool_1, tool_2, ..., tool_N).
        """
        t0 = time.perf_counter()
        specs = self.plan_tools_for_query(query)

        async def _orchestrate() -> List[Dict[str, Any]]:
            coros = [self._execute_tool_async(spec) for spec in specs]
            return await asyncio.gather(*coros, return_exceptions=False)

        try:
            results = await asyncio.wait_for(_orchestrate(), timeout=self.global_run_timeout)
            timed_out = False
        except asyncio.TimeoutError:
            results = [{"status": "TIMEOUT", "error": f"Agent run exceeded global timeout of {self.global_run_timeout}s"}]
            timed_out = True
        except asyncio.CancelledError:
            wall_clock_ms = (time.perf_counter() - t0) * 1000.0
            return AgentRunResult(
                query=query,
                mode="parallel",
                tools_called=[s.tool_name for s in specs],
                tool_results=[],
                final_action_plan={},
                wall_clock_latency_ms=round(wall_clock_ms, 2),
                total_tool_latency_sum_ms=0.0,
                concurrency_efficiency_pct=0.0,
                cancelled=True,
            )

        wall_clock_ms = (time.perf_counter() - t0) * 1000.0
        total_sum_ms = sum(float(r.get("latency_ms", 0.0) or 0.0) for r in results)
        efficiency = (
            ((total_sum_ms - wall_clock_ms) / total_sum_ms * 100.0)
            if total_sum_ms > 0 and total_sum_ms > wall_clock_ms
            else 0.0
        )

        action_plan = self._formulate_action_plan(query, results)

        return AgentRunResult(
            query=query,
            mode="parallel",
            tools_called=[s.tool_name for s in specs],
            tool_results=results,
            final_action_plan=action_plan,
            wall_clock_latency_ms=round(wall_clock_ms, 2),
            total_tool_latency_sum_ms=round(total_sum_ms, 2),
            concurrency_efficiency_pct=round(efficiency, 1),
            timed_out=timed_out,
        )

    def _formulate_action_plan(self, query: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes diagnostic evidence into a structured SRE remediation plan."""
        affected = "payment-api"
        sev = "SEV-2"
        runbook = "RUNBOOK-02"

        for r in tool_results:
            if r.get("tool") == "search_runbooks" and r.get("matches"):
                m = r["matches"][0]
                runbook = m.get("runbook_id", "RUNBOOK-01")
            elif r.get("tool") == "query_telemetry_db" and r.get("data"):
                item = r["data"][0] if isinstance(r["data"], list) else {}
                affected = item.get("name") or item.get("service") or affected

        return {
            "severity": sev,
            "affected_service": affected,
            "root_cause_hypothesis": f"Evidence synthesized from {len(tool_results)} concurrent diagnostic streams.",
            "recommended_action": "Drain connection pool backlog and initiate rolling pod restart.",
            "runbook_citation": runbook,
            "requires_approval": True,
        }
