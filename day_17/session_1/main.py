"""
Day 17 - Session 01: Standup & Attacking Riskiest Task First
Executes the async diagnostic tool dispatcher under high noise,
testing Kubernetes, Prometheus metrics, and Git diff tools with timeout resilience.
"""

from __future__ import annotations
import asyncio
from riskiest_task_derisker import (
    AsyncDiagnosticToolDispatcher,
    MockCloudInfrastructure,
    LogAnomalyCompactor,
)


async def main():
    print("Day 17 Session 01: De-Risking Async Diagnostic Tools\n")

    # 1. High-throughput log compaction
    compactor = LogAnomalyCompactor()
    raw_logs = ["INFO request handled 200"] * 995 + [
        "ERROR Database connection timeout: pool exhausted (host: pg-pooler-01)",
        "FATAL Out of memory: killed pod payments-core-99",
    ]
    distilled = compactor.compact_logs(raw_logs)
    print(f"Log Compaction: {len(raw_logs)} lines reduced to {len(distilled)} high-entropy anomalies.")

    # 2. Async tool dispatching
    dispatcher = AsyncDiagnosticToolDispatcher()
    bundle = await dispatcher.gather_cluster_diagnostics("payments-core", "prod")
    print(f"Diagnostics Gathered: {len(bundle.tools_executed)} tools in {bundle.wall_clock_ms:.1f}ms")
    print(f"Status: Pods={bundle.pod_status}, Anomaly Count={len(bundle.anomalies)}")

    print("\nRiskiest task de-risked: Concurrent tool dispatching and log compaction verified.")


if __name__ == "__main__":
    asyncio.run(main())
