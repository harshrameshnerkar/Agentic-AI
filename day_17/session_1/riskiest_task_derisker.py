"""
Day 17 - Session 1: Riskiest Task De-Risker
Runs concurrent diagnostic tools with timeout circuit breakers and log anomaly extraction.
"""

import asyncio
from dataclasses import dataclass, field
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DiagnosticBundle:
    incident_id: str
    service: str
    namespace: str
    pod_telemetry: Dict[str, Any]
    metrics_telemetry: Dict[str, Any]
    git_telemetry: Dict[str, Any]
    log_anomalies: List[Dict[str, Any]]
    total_execution_ms: float
    circuit_breaker_fallbacks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "service": self.service,
            "namespace": self.namespace,
            "pod_telemetry": self.pod_telemetry,
            "metrics_telemetry": self.metrics_telemetry,
            "git_telemetry": self.git_telemetry,
            "log_anomalies": self.log_anomalies,
            "total_execution_ms": round(self.total_execution_ms, 2),
            "circuit_breaker_fallbacks": self.circuit_breaker_fallbacks,
        }


class LogAnomalyCompactor:
    """Scans noisy logs and extracts fatal error stack traces."""

    FATAL_PATTERNS = [
        re.compile(r"(?i)(java\.lang\.OutOfMemoryError|FatalProcessOutOfMemory|exit code 137)"),
        re.compile(r"(?i)(HikariPool.*Connection is not available|FATAL: remaining connection slots)"),
        re.compile(r"(?i)(upstream timed out \(110: Connection timed out\)|504 Gateway Time-out)"),
        re.compile(r"(?i)(evicted_keys.*spiking|CONFIG SET maxmemory|Redis BigKey alert)"),
        re.compile(r"(?i)(Exception|Error|Fatal|Deadlock|CrashLoopBackOff)"),
    ]

    @classmethod
    def compact_logs(cls, raw_logs: List[str], max_anomalies: int = 5) -> List[Dict[str, Any]]:
        extracted: Dict[str, Dict[str, Any]] = {}
        for idx, line in enumerate(raw_logs):
            for pat in cls.FATAL_PATTERNS:
                if pat.search(line):
                    start = max(0, idx - 1)
                    end = min(len(raw_logs), idx + 2)
                    fp = line.strip()[:100]
                    if fp in extracted:
                        extracted[fp]["occurrences"] += 1
                    else:
                        extracted[fp] = {
                            "line_number": idx + 1,
                            "headline": line.strip(),
                            "context_snippet": "\n".join(raw_logs[start:end]),
                            "occurrences": 1,
                        }
                    break

        return sorted(extracted.values(), key=lambda x: x["occurrences"], reverse=True)[:max_anomalies]


class MockCloudInfrastructure:
    """Mock cloud APIs for Kubernetes, Prometheus, Git, and logs."""

    def __init__(self, simulate_network_delay: float = 0.1):
        self.delay = simulate_network_delay

    async def get_pod_status(self, service: str, namespace: str, simulate_hang: bool = False) -> Dict[str, Any]:
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)
        return {
            "service": service,
            "namespace": namespace,
            "phase": "CrashLoopBackOff",
            "last_state": {"terminated": {"reason": "OOMKilled", "exit_code": 137}},
        }

    async def query_metrics(self, service: str, simulate_hang: bool = False) -> Dict[str, Any]:
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)
        return {
            "service": service,
            "memory_ratio": 0.99,
            "p99_latency_ms": 3400.0,
        }

    async def get_git_diff(self, service: str, simulate_hang: bool = False) -> Dict[str, Any]:
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)
        return {
            "service": service,
            "commit_sha": "7f8b9a2d3c4e",
            "diff_summary": "+128 lines in session_cache.go",
        }

    async def fetch_and_compact_logs(self, service: str, num_lines: int = 50000, simulate_hang: bool = False) -> List[Dict[str, Any]]:
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)

        logs = [f"[INFO] req_{i} status=200" for i in range(num_lines - 5)]
        logs.insert(25000, "java.lang.OutOfMemoryError: Java heap space at SessionBuffer:142")
        logs.insert(25001, "Container terminated by Linux OOM-killer (exit code 137)")
        return LogAnomalyCompactor.compact_logs(logs, max_anomalies=5)


class AsyncDiagnosticToolDispatcher:
    """Dispatches diagnostic tools concurrently with timeout resilience."""

    def __init__(self, cloud_api: Optional[MockCloudInfrastructure] = None, tool_timeout_sec: float = 1.5):
        self.cloud_api = cloud_api or MockCloudInfrastructure()
        self.timeout = tool_timeout_sec

    async def _safe_run(self, name: str, coro) -> Tuple[Any, Optional[str]]:
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout), None
        except asyncio.TimeoutError:
            return None, f"CIRCUIT_BREAKER_TIMEOUT: {name} exceeded {self.timeout}s"
        except Exception as e:
            return None, f"TOOL_ERROR: {name} failed: {e}"

    async def dispatch_all_diagnostics(
        self, incident_id: str, service: str, namespace: str = "prod-core", simulate_faulty_tool: Optional[str] = None
    ) -> DiagnosticBundle:
        t0 = time.perf_counter()
        fallbacks: List[str] = []

        pod_task = self._safe_run("pod", self.cloud_api.get_pod_status(service, namespace, simulate_faulty_tool == "pod"))
        metrics_task = self._safe_run("metrics", self.cloud_api.query_metrics(service, simulate_faulty_tool == "metrics"))
        git_task = self._safe_run("git", self.cloud_api.get_git_diff(service, simulate_faulty_tool == "git"))
        logs_task = self._safe_run("logs", self.cloud_api.fetch_and_compact_logs(service, simulate_hang=(simulate_faulty_tool == "logs")))

        (pod, pod_err), (metrics, metrics_err), (git, git_err), (logs, logs_err) = await asyncio.gather(
            pod_task, metrics_task, git_task, logs_task
        )

        if pod_err:
            fallbacks.append(pod_err)
            pod = {"phase": "UNKNOWN"}
        if metrics_err:
            fallbacks.append(metrics_err)
            metrics = {}
        if git_err:
            fallbacks.append(git_err)
            git = {}
        if logs_err:
            fallbacks.append(logs_err)
            logs = []

        return DiagnosticBundle(
            incident_id=incident_id,
            service=service,
            namespace=namespace,
            pod_telemetry=pod or {},
            metrics_telemetry=metrics or {},
            git_telemetry=git or {},
            log_anomalies=logs or [],
            total_execution_ms=(time.perf_counter() - t0) * 1000.0,
            circuit_breaker_fallbacks=fallbacks,
        )


if __name__ == "__main__":
    dispatcher = AsyncDiagnosticToolDispatcher()
    bundle = asyncio.run(dispatcher.dispatch_all_diagnostics("INC-01", "auth-service"))
    print(json.dumps(bundle.to_dict(), indent=2))
