"""
Day 13 - Session 3: Distributed Cross-Replica Rate Limiting & Backoff
====================================================================
Implements:
  1. Distributed Token Bucket Algorithm (coordinating across N stateless replicas)
  2. Rate limit breach prevention (enforcing global RPM/TPM across workers)
  3. Exponential Backoff with Full Jitter (handling upstream 429 Too Many Requests)
  4. Non-blocking token reservation with acquire timeouts
"""

import time
import random
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RateLimitStatus:
    allowed: bool
    current_tokens: float
    max_tokens: int
    wait_time_sec: float
    retry_count: int


class DistributedTokenBucket:
    """
    Simulated Distributed Token Bucket (shared state equivalent to Redis atomic Lua script).
    Coordinates rate limiting across all agent replicas to prevent 429 penalties.
    """

    def __init__(self, rate_limit_rpm: int = 60, burst_capacity: Optional[int] = None):
        self.capacity = burst_capacity or rate_limit_rpm
        self.refill_rate = rate_limit_rpm / 60.0  # tokens added per second
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def try_acquire(self, tokens_requested: int = 1) -> RateLimitStatus:
        """Attempts to reserve tokens. Returns whether allowed and remaining capacity."""
        async with self._lock:
            await self._refill()
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return RateLimitStatus(
                    allowed=True,
                    current_tokens=round(self.tokens, 2),
                    max_tokens=self.capacity,
                    wait_time_sec=0.0,
                    retry_count=0,
                )
            else:
                deficit = tokens_requested - self.tokens
                wait_sec = deficit / self.refill_rate
                return RateLimitStatus(
                    allowed=False,
                    current_tokens=round(self.tokens, 2),
                    max_tokens=self.capacity,
                    wait_time_sec=round(wait_sec, 3),
                    retry_count=0,
                )

    async def acquire_with_backoff(
        self,
        max_retries: int = 4,
        base_delay_sec: float = 0.1,
        max_delay_sec: float = 2.0,
    ) -> RateLimitStatus:
        """
        Acquires token with Full Jitter Exponential Backoff.
        Jitter prevents 'thundering herd' when multiple replicas resume simultaneously.
        """
        for attempt in range(max_retries + 1):
            status = await self.try_acquire(tokens_requested=1)
            if status.allowed:
                status.retry_count = attempt
                return status

            if attempt == max_retries:
                status.retry_count = attempt
                return status

            # Calculate Exponential Backoff with Full Jitter: Uniform(0, min(max_delay, base * 2^attempt))
            exp_delay = min(max_delay_sec, base_delay_sec * (2 ** attempt))
            jittered_sleep = random.uniform(0.01, exp_delay)
            await asyncio.sleep(jittered_sleep)

        return RateLimitStatus(allowed=False, current_tokens=0.0, max_tokens=self.capacity, wait_time_sec=1.0, retry_count=max_retries)
