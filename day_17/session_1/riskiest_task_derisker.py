"""Day 17 - Session 1: Riskiest Task De-Risker.

Attacks the single riskiest technical assumption of Sprint 1:
Concurrent async diagnostic tool integration, high-noise log compaction (50k lines),
and circuit-breaker timeout resilience across Kubernetes, Prometheus, Git, and Splunk.
"""

import asyncio
from dataclasses import dataclass, field
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DiagnosticBundle:
    """Standardized schema output from concurrent diagnostic tool dispatch."""

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
    """High-throughput log scanner: sifts through 50,000 noisy lines and extracts fatal traces."""

    FATAL_PATTERNS = [
        re.compile(r"(?i)(java\.lang\.OutOfMemoryError|FatalProcessOutOfMemory|exit code 137)"),
        re.compile(r"(?i)(HikariPool.*Connection is not available|FATAL: remaining connection slots)"),
        re.compile(r"(?i)(upstream timed out \(110: Connection timed out\)|504 Gateway Time-out)"),
        re.compile(r"(?i)(evicted_keys.*spiking|CONFIG SET maxmemory|Redis BigKey alert)"),
        re.compile(r"(?i)(Exception|Error|Fatal|Deadlock|CrashLoopBackOff)"),
    ]

    @classmethod
    def compact_logs(
        cls, raw_logs: List[str], max_anomalies: int = 5
    ) -> List[Dict[str, Any]]:
        """Scans raw log lines, isolates fatal stack traces, and deduplicates occurrences."""
        extracted: Dict[str, Dict[str, Any]] = {}

        for idx, line in enumerate(raw_logs):
            for pattern in cls.FATAL_PATTERNS:
                if pattern.search(line):
                    # Extract 2 lines before and 2 lines after for stack context
                    start = max(0, idx - 1)
                    end = min(len(raw_logs), idx + 2)
                    context_snippet = "\n".join(raw_logs[start:end])
                    fingerprint = line.strip()[:100]

                    if fingerprint in extracted:
                        extracted[fingerprint]["occurrences"] += 1
                    else:
                        extracted[fingerprint] = {
                            "line_number": idx + 1,
                            "match_type": pattern.pattern[:35],
                            "headline": line.strip(),
                            "context_snippet": context_snippet,
                            "occurrences": 1,
                        }
                    break

        # Return top N distinct anomalies sorted by occurrences
        ranked = sorted(
            extracted.values(), key=lambda x: x["occurrences"], reverse=True
        )[:max_anomalies]
        return ranked


class MockCloudInfrastructure:
    """Simulates real-world Kubernetes, Prometheus, Git, and Splunk API endpoints."""

    def __init__(self, simulate_network_delay: float = 0.25):
        self.delay = simulate_network_delay

    async def get_pod_status(
        self, service: str, namespace: str, simulate_hang: bool = False
    ) -> Dict[str, Any]:
        """Queries Kubernetes API for pod container states and restart counts."""
        if simulate_hang:
            await asyncio.sleep(5.0)  # Trigger timeout
        await asyncio.sleep(self.delay)

        return {
            "service": service,
            "namespace": namespace,
            "pod_name": f"{service}-canary-7b8df9c4",
            "phase": "CrashLoopBackOff",
            "ready": False,
            "restart_count": 5,
            "last_state": {
                "terminated": {
                    "reason": "OOMKilled",
                    "exit_code": 137,
                    "finished_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
                }
            },
            "limits": {"memory": "2Gi", "cpu": "1000m"},
            "requests": {"memory": "1Gi", "cpu": "500m"},
        }

    async def query_metrics(
        self, service: str, simulate_hang: bool = False
    ) -> Dict[str, Any]:
        """Queries Prometheus/Datadog for CPU, memory, and latency time-series."""
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)

        return {
            "service": service,
            "cpu_utilization_pct": 74.5,
            "memory_usage_mb": 2046.2,
            "memory_limit_mb": 2048.0,
            "memory_ratio": 0.999,
            "p99_latency_ms": 3480.0,
            "error_rate_5xx_pct": 14.8,
            "trend": "MONOTONIC_SPIKE",
        }

    async def get_git_diff(
        self, service: str, simulate_hang: bool = False
    ) -> Dict[str, Any]:
        """Queries ArgoCD and GitHub API for recent deployment commits."""
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)

        return {
            "service": service,
            "deployed_at": "18 minutes ago",
            "commit_sha": "7f8b9a2d3c4e",
            "author": "junior-dev@enterprise.com",
            "commit_message": "feat(cache): add in-memory session token buffer",
            "diff_summary": "+128 lines in session_cache.go (Unbounded slice accumulation)",
        }

    async def fetch_and_compact_logs(
        self, service: str, num_lines: int = 50000, simulate_hang: bool = False
    ) -> List[Dict[str, Any]]:
        """Simulates ingestion of 50,000 noisy log lines and extracts fatal traces."""
        if simulate_hang:
            await asyncio.sleep(5.0)
        await asyncio.sleep(self.delay)

        # Generate 50,000 simulated log lines with embedded fatal stack traces
        logs = [
            f"2026-10-08T09:30:{i%60:02d}.{i%1000:03d}Z [INFO] request_id=req_{i:06d} path=/healthz status=200 duration=2ms"
            for i in range(num_lines - 10)
        ]

        # Inject real fatal anomalies
        fatal_lines = [
            "2026-10-08T09:30:14.281Z [FATAL] java.lang.OutOfMemoryError: Java heap space at com.auth.SessionBuffer.append(SessionBuffer.java:142)",
            "2026-10-08T09:30:14.282Z [ERROR] Container terminated by Linux OOM-killer (exit code 137)",
            "2026-10-08T09:30:15.109Z [FATAL] java.lang.OutOfMemoryError: Java heap space at com.auth.SessionBuffer.append(SessionBuffer.java:142)",
            "2026-10-08T09:30:16.890Z [ERROR] Pod entered CrashLoopBackOff: back-off 40s restarting failed container=auth-service",
            "2026-10-08T09:30:18.012Z [FATAL] java.lang.OutOfMemoryError: Java heap space at com.auth.SessionBuffer.append(SessionBuffer.java:142)",
        ]
        # Distribute into log stream
        for idx, fl in enumerate(fatal_lines):
            insert_pos = (idx + 1) * 8000
            logs.insert(insert_pos, fl)

        # Run high-throughput compaction
        compacted = LogAnomalyCompactor.compact_logs(logs, max_anomalies=5)
        return compacted


class AsyncDiagnosticToolDispatcher:
    """Dispatches diagnostic tools concurrently with circuit-breaking timeout guards."""

    def __init__(
        self,
        cloud_api: Optional[MockCloudInfrastructure] = None,
        tool_timeout_sec: float = 2.0,
    ):
        self.cloud_api = cloud_api or MockCloudInfrastructure()
        self.timeout = tool_timeout_sec

    async def _safe_execute(self, tool_name: str, coro) -> Tuple[Any, Optional[str]]:
        """Executes a coroutine with timeout and exception containment."""
        try:
            result = await asyncio.wait_for(coro, timeout=self.timeout)
            return result, None
        except asyncio.TimeoutError:
            return None, f"CIRCUIT_BREAKER_TIMEOUT: {tool_name} exceeded {self.timeout}s"
        except Exception as e:
            return None, f"TOOL_EXECUTION_ERROR: {tool_name} failed with {type(e).__name__}: {str(e)}"

    async def dispatch_all_diagnostics(
        self,
        incident_id: str,
        service: str,
        namespace: str = "prod-core",
        simulate_faulty_tool: Optional[str] = None,
    ) -> DiagnosticBundle:
        """Executes pod check, metrics, git diff, and log compaction in parallel."""
        t0 = time.perf_counter()
        fallbacks: List[str] = []

        # Configure coroutines with optional fault injection
        coro_pod = self.cloud_api.get_pod_status(
            service, namespace, simulate_hang=(simulate_faulty_tool == "pod")
        )
        coro_metrics = self.cloud_api.query_metrics(
            service, simulate_hang=(simulate_faulty_tool == "metrics")
        )
        coro_git = self.cloud_api.get_git_diff(
            service, simulate_hang=(simulate_faulty_tool == "git")
        )
        coro_logs = self.cloud_api.fetch_and_compact_logs(
            service, num_lines=50000, simulate_hang=(simulate_faulty_tool == "logs")
        )

        # Dispatch all 4 in parallel via asyncio.gather
        results = await asyncio.gather(
            self._safe_execute("get_pod_status", coro_pod),
            self._safe_execute("query_metrics", coro_metrics),
            self._safe_execute("get_git_diff", coro_git),
            self._safe_execute("fetch_and_compact_logs", coro_logs),
            return_exceptions=True,
        )

        # Process results and circuit-breaker fallbacks
        pod_res, pod_err = results[0]
        if pod_err:
            fallbacks.append(pod_err)
            pod_res = {"error": pod_err, "service": service, "phase": "UNKNOWN"}

        metrics_res, metrics_err = results[1]
        if metrics_err:
            fallbacks.append(metrics_err)
            metrics_res = {"error": metrics_err, "trend": "UNAVAILABLE"}

        git_res, git_err = results[2]
        if git_err:
            fallbacks.append(git_err)
            git_res = {"error": git_err, "diff_summary": "UNAVAILABLE"}

        logs_res, logs_err = results[3]
        if logs_err:
            fallbacks.append(logs_err)
            logs_res = [{"error": logs_err, "headline": "LOG_EXTRACTION_UNAVAILABLE"}]

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return DiagnosticBundle(
            incident_id=incident_id,
            service=service,
            namespace=namespace,
            pod_telemetry=pod_res,
            metrics_telemetry=metrics_res,
            git_telemetry=git_res,
            log_anomalies=logs_res,
            total_execution_ms=elapsed_ms,
            circuit_breaker_fallbacks=fallbacks,
        )


async def main_demo():
    dispatcher = AsyncDiagnosticToolDispatcher()
    print("Executing parallel diagnostic dispatch over 50,000 log lines...")
    bundle = await dispatcher.dispatch_all_diagnostics(
        incident_id="INC-2026-992", service="auth-service", namespace="prod-core"
    )
    print(json.dumps(bundle.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(main_demo())
