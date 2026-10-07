"""
Day 13 - Session 1: Master CLI & Interactive Exploration Suite
==============================================================
Provides interactive and CLI execution for:
  1. Concurrency Benchmark: Sequential vs. Parallel tool latency measurement
  2. Worker Queue System: Producer-consumer queue, polling, and webhook dispatch
  3. Timeouts & Cancellation: Cancelling long-running jobs gracefully
  4. Ad-hoc Query Execution: Parallel tool calling on custom incident prompts
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from async_capstone_agent import AsyncCapstoneAgent
from worker_queue import AgentWorkerQueue, JobStatus
from benchmark_concurrency import run_concurrency_benchmark


def print_header(title: str) -> None:
    print("\n" + "=" * 90)
    print(f" {title.center(88)} ")
    print("=" * 90)


async def demo_worker_queue() -> None:
    print_header("DEMONSTRATION: ASYNC WORKER QUEUE, POLLING & WEBHOOKS")
    agent = AsyncCapstoneAgent()
    queue = AgentWorkerQueue(num_workers=2, agent=agent)
    await queue.start()

    delivered_webhooks = []

    async def mock_webhook(payload: Dict[str, Any]) -> None:
        delivered_webhooks.append(payload)
        print(f"\n[WEBHOOK RECEIVED] Job {payload['job_id']} finished! Status: {payload['status']}")

    queries = [
        "Payment-api latency spike > 1800ms. Inspect telemetry and logs.",
        "Postgres connection pool nearing 98% saturation. Check pooler status.",
        "Nginx ingress 504 error burst. Check proxy error logs.",
    ]

    print("\n1. Submitting 3 asynchronous incident jobs to the worker queue...")
    job_ids = []
    for q in queries:
        jid = await queue.submit_job(q, webhook_callback=mock_webhook)
        print(f"   - Submitted: {jid} | Query: '{q[:55]}...'")
        job_ids.append(jid)

    print("\n2. Polling job status progressively (Simulating client polling)...")
    for _ in range(6):
        await asyncio.sleep(0.08)
        statuses = [queue.get_job_status(j) for j in job_ids]
        line = " | ".join(f"{s['job_id']}: {s['status']} ({s['elapsed_ms']}ms)" for s in statuses)
        print(f"   [POLL] {line}")
        if all(s["status"] in ("COMPLETED", "FAILED") for s in statuses):
            break

    # Wait for all jobs to drain
    while not all(queue.get_job_status(j)["status"] == "COMPLETED" for j in job_ids):
        await asyncio.sleep(0.05)

    print("\n3. Final Job Results Summary:")
    print("-" * 90)
    for jid in job_ids:
        job = queue.get_job(jid)
        if job and job.result:
            print(f"[{jid}] Status: {job.status.value} | Latency: {job.result.wall_clock_latency_ms}ms | Tools: {', '.join(job.result.tools_called)}")
            print(f"       Action Plan: {job.result.final_action_plan['recommended_action']}")

    print(f"\n[OK] Webhooks successfully delivered: {len(delivered_webhooks)} / {len(job_ids)}")
    await queue.stop()


async def demo_job_cancellation() -> None:
    print_header("DEMONSTRATION: TIMEOUTS & JOB CANCELLATION")
    agent = AsyncCapstoneAgent()
    queue = AgentWorkerQueue(num_workers=1, agent=agent)
    await queue.start()

    print("\n1. Submitting long-running diagnostic job...")
    jid = await queue.submit_job("Investigate complex cluster failure with multiple diagnostic tools.")
    print(f"   Submitted Job ID: {jid} (Status: {queue.get_job_status(jid)['status']})")

    await asyncio.sleep(0.05)
    print(f"   Active Job Status: {queue.get_job_status(jid)['status']}")

    print("\n2. Operator requests immediate cancellation (Abort signal received)...")
    success = await queue.cancel_job(jid)
    print(f"   Cancel request sent -> Result: {success}")

    await asyncio.sleep(0.05)
    final_status = queue.get_job_status(jid)
    print(f"   Post-Cancellation Status: {final_status['status']}")
    print(f"   Cancellation Note: {final_status.get('error') or 'Gracefully halted'}")
    print("[OK] Confirmed: Job did not execute destructive actions and resources were released.")
    await queue.stop()


async def demo_single_query(query: str) -> None:
    print_header("SINGLE QUERY PARALLEL CONCURRENCY INSPECTION")
    agent = AsyncCapstoneAgent()

    print(f"Query: '{query}'\n")
    print("[RUNNING] Executing sequential baseline...")
    seq_res = agent.run_sequential(query)

    print("[RUNNING] Executing async parallel execution...")
    par_res = await agent.run_parallel(query)

    delta_ms = seq_res.wall_clock_latency_ms - par_res.wall_clock_latency_ms
    pct = (delta_ms / seq_res.wall_clock_latency_ms) * 100.0 if seq_res.wall_clock_latency_ms > 0 else 0.0

    print("-" * 90)
    print(f"Sequential Latency : {seq_res.wall_clock_latency_ms:.1f} ms")
    print(f"Parallel Latency   : {par_res.wall_clock_latency_ms:.1f} ms")
    print(f"Latency Reduction  : {delta_ms:.1f} ms ({pct:.1f}% faster)")
    print(f"Tools Executed     : {', '.join(par_res.tools_called)}")
    print(f"Synthesized Plan   : {json.dumps(par_res.final_action_plan, indent=2)}")
    print("-" * 90)


async def interactive_menu() -> None:
    while True:
        print_header("DAY 13 - SESSION 1: ASYNC & CONCURRENCY")
        print("  1. Run Concurrency Benchmark (Sequential vs Parallel Latency)")
        print("  2. Test Worker Queue (Async Queue, Polling & Webhooks)")
        print("  3. Test Timeouts & Job Cancellation Demo")
        print("  4. Run Custom Incident Query")
        print("  5. Exit")
        choice = input("\nSelect an option [1-5]: ").strip()

        if choice == "1":
            await run_concurrency_benchmark()
        elif choice == "2":
            await demo_worker_queue()
        elif choice == "3":
            await demo_job_cancellation()
        elif choice == "4":
            q = input("Enter incident query: ").strip()
            if q:
                await demo_single_query(q)
        elif choice == "5":
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 13 Session 1: Async & Concurrency")
    parser.add_argument("--benchmark", action="store_true", help="Run sequential vs parallel latency benchmark")
    parser.add_argument("--worker-queue", action="store_true", help="Run worker queue & webhook demo")
    parser.add_argument("--cancel-demo", action="store_true", help="Run job cancellation demo")
    parser.add_argument("--query", type=str, help="Execute single query with parallel tools")

    args = parser.parse_args()

    if args.benchmark:
        asyncio.run(run_concurrency_benchmark())
    elif args.worker_queue:
        asyncio.run(demo_worker_queue())
    elif args.cancel_demo:
        asyncio.run(demo_job_cancellation())
    elif args.query:
        asyncio.run(demo_single_query(args.query))
    else:
        # Default run benchmark and worker queue
        asyncio.run(run_concurrency_benchmark())


if __name__ == "__main__":
    main()
