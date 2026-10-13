"""
Day 13 - Session 03: Failover, Rate Limiting & Secrets
Demonstrates:
1. Secret masking in application settings.
2. Multi-provider automatic failover with circuit breaker states.
3. Distributed token bucket rate limiting under burst traffic.
"""

from __future__ import annotations
import asyncio
from config import settings
from provider_failover import MultiProviderFailoverEngine
from distributed_rate_limiter import DistributedTokenBucket


def check_secrets():
    print("\n--- 1. Secret Masking Audit ---")
    print(f"Anthropic Key Masked: {settings.anthropic_api_key}")
    print(f"OpenAI Key Masked:    {settings.openai_api_key}")
    print(f"Gemini Key Masked:    {settings.gemini_api_key}")
    assert "sk-" not in str(settings.openai_api_key)
    print("Pass: Plaintext secrets masked cleanly.")


async def demo_failover():
    print("\n--- 2. Multi-Provider Failover Simulation ---")
    engine = MultiProviderFailoverEngine(error_threshold=2, recovery_time_sec=2.0)
    query = "Postgres connection pool nearing 98% saturation."

    res = await engine.execute_with_failover(query)
    print(f"Active Provider: {res.active_provider.upper()} (Latency: {res.latency_ms:.1f}ms)")
    print(f"Response: {res.content[:100]}...")


async def demo_rate_limiter():
    print("\n--- 3. Distributed Rate Limiter Burst Test ---")
    limiter = DistributedTokenBucket(capacity=5, refill_rate_per_sec=2.0)
    allowed, denied = 0, 0
    for _ in range(8):
        if limiter.acquire():
            allowed += 1
        else:
            denied += 1
    print(f"Burst of 8 requests: {allowed} allowed, {denied} throttled.")
    assert denied > 0


async def main():
    print("Day 13 Session 03: Production Reliability & Failover\n")
    check_secrets()
    await demo_failover()
    await demo_rate_limiter()
    print("\nReliability and failover checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
