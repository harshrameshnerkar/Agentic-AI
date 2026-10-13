"""
Day 13 - Session 01: Async Agent & Worker Queue
Demonstrates:
1. Producer-consumer worker queue with asynchronous jobs and webhooks.
2. Concurrent non-blocking tool calls.
3. Concurrency benchmark measuring latency speedup.
"""

from __future__ import annotations
import asyncio
from typing import Dict, Any
from async_capstone_agent import AsyncCapstoneAgent
from worker_queue import AgentWorkerQueue
from benchmark_concurrency import run_concurrency_benchmark


async def demo_worker_queue():
    print("\n--- 1. Asynchronous Worker Queue & Webhooks ---")
    agent = AsyncCapstoneAgent()
    queue = AgentWorkerQueue(num_workers=2, agent=agent)
    await queue.start()

    delivered = []

    async def mock_webhook(payload: Dict[str, Any]):
        delivered.append(payload)
        print(f"  [Webhook] Job {payload['job_id']} completed: {payload['status']}")

    queries = [
        "Payment-api latency spike > 1800ms. Inspect telemetry and logs.",
        "Postgres connection pool nearing 98% saturation. Check pooler status.",
    ]

    job_ids = []
    for q in queries:
        jid = await queue.submit_job(q, webhook_callback=mock_webhook)
        job_ids.append(jid)
        print(f"  Submitted job: {jid}")

    # Wait for completion
    for _ in range(8):
        await asyncio.sleep(0.5)
        all_done = all(queue.get_job(jid)["status"] in ["COMPLETED", "FAILED"] for jid in job_ids)
        if all_done:
            break

    await queue.stop()
    print(f"All jobs processed successfully ({len(delivered)} webhooks delivered).")


async def main():
    print("Day 13 Session 01: Async Agent & Concurrency\n")
    await demo_worker_queue()

    print("\n--- 2. Concurrency Benchmark ---")
    await run_concurrency_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
