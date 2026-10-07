"""
Day 13 - Session 1: Asynchronous Worker Queue & Job Lifecycle Management
========================================================================
Implements:
  1. Worker Queues for Long-Running Agent Runs (Producer-Consumer via asyncio.Queue)
  2. Job Lifecycle States: PENDING -> RUNNING -> COMPLETED | FAILED | CANCELLED
  3. Job Status Polling API (get_job_status, get_job_result)
  4. Webhook Notification Callbacks (simulated async HTTP callback on completion)
  5. Timeouts and Dynamic Job Cancellation (cancel_job)
"""

import os
import sys
import asyncio
import time
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from async_capstone_agent import AsyncCapstoneAgent, AgentRunResult


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class AgentJob:
    job_id: str
    query: str
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[AgentRunResult] = None
    error: Optional[str] = None
    webhook_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    webhook_delivered: bool = False
    task_handle: Optional[asyncio.Task] = None


class AgentWorkerQueue:
    """
    Production-Grade Worker Queue System for Asynchronous Agent Execution.
    Decouples client request ingress from heavy multi-tool reasoning runs.
    """

    def __init__(self, num_workers: int = 3, agent: Optional[AsyncCapstoneAgent] = None):
        self.num_workers = num_workers
        self.agent = agent or AsyncCapstoneAgent()
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.jobs: Dict[str, AgentJob] = {}
        self.worker_tasks: List[asyncio.Task] = []
        self._is_running = False

    async def start(self) -> None:
        """Starts worker pool coroutines."""
        if self._is_running:
            return
        self._is_running = True
        self.worker_tasks = [
            asyncio.create_task(self._worker_loop(worker_id=i + 1))
            for i in range(self.num_workers)
        ]

    async def stop(self) -> None:
        """Gracefully drains and stops worker tasks."""
        self._is_running = False
        for t in self.worker_tasks:
            t.cancel()
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

    async def submit_job(
        self,
        query: str,
        webhook_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> str:
        """
        Enqueues an agent run job. Returns immediately with unique job_id.
        Client can either poll status or receive webhook notification.
        """
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        job = AgentJob(
            job_id=job_id,
            query=query,
            webhook_callback=webhook_callback,
        )
        self.jobs[job_id] = job
        await self.queue.put(job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[AgentJob]:
        """Returns the full job state object."""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Polling endpoint: returns current status and runtime telemetry."""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found."}

        elapsed = 0.0
        if job.started_at:
            end = job.completed_at or time.time()
            elapsed = round((end - job.started_at) * 1000.0, 1)

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "query": job.query,
            "elapsed_ms": elapsed,
            "has_result": job.result is not None,
            "webhook_delivered": job.webhook_delivered,
            "error": job.error,
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancels a pending or active job gracefully."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.completed_at = time.time()
            return True

        if job.status == JobStatus.RUNNING and job.task_handle:
            job.task_handle.cancel()
            job.status = JobStatus.CANCELLED
            job.completed_at = time.time()
            return True

        return False

    async def _worker_loop(self, worker_id: int) -> None:
        """Background worker consuming jobs from queue."""
        while self._is_running:
            try:
                job_id = await self.queue.get()
            except asyncio.CancelledError:
                break

            job = self.jobs.get(job_id)
            if not job or job.status == JobStatus.CANCELLED:
                self.queue.task_done()
                continue

            job.status = JobStatus.RUNNING
            job.started_at = time.time()

            try:
                # Wrap execution in an explicit task so it can be cancelled
                task = asyncio.create_task(self.agent.run_parallel(job.query))
                job.task_handle = task
                result = await task

                if result.cancelled:
                    job.status = JobStatus.CANCELLED
                else:
                    job.result = result
                    job.status = JobStatus.COMPLETED
            except asyncio.CancelledError:
                job.status = JobStatus.CANCELLED
                job.error = "Job cancelled by operator request."
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
            finally:
                job.completed_at = time.time()
                self.queue.task_done()

                # Trigger Webhook Callback if registered
                if job.webhook_callback and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    try:
                        payload = {
                            "job_id": job.job_id,
                            "status": job.status.value,
                            "query": job.query,
                            "result": job.result.__dict__ if job.result else None,
                        }
                        await job.webhook_callback(payload)
                        job.webhook_delivered = True
                    except Exception as wh_err:
                        job.error = f"Webhook dispatch error: {wh_err}"
