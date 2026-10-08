# SOP-SRE-412: Redis Cache Eviction Storm & Cold-Cache Thundering Herd

**Service:** `redis-cluster`, `session-cache`, `catalog-cache`  
**Severity:** Sev-2  
**Last Updated:** September 5, 2026  
**Status:** ACTIVE / VERIFIED  
**Owner:** Caching & High-Throughput Storage  

---

## 1. Symptoms & Diagnostic Triggers
- Redis metric `evicted_keys` spiking rapidly (> 50,000 keys/sec).
- Cache hit ratio drops from 98.5% down to < 40.0%.
- Primary database CPU spikes to 100% due to un-cached queries hitting PostgreSQL.

## 2. Immediate Diagnostic Steps
1. Check Redis memory usage:
   `redis-cli -h redis-cluster.internal info memory`
2. Inspect top key size distribution:
   `redis-cli -h redis-cluster.internal --bigkeys`
3. DO NOT execute `FLUSHALL` or `FLUSHDB` — doing so causes catastrophic database failure.

## 3. Recommended Remediation Plan
- **Tier 1 (Read-Only):** Identify oversized keys or keys without TTLs.
- **Tier 2 (Low Risk):** Dynamically increase `maxmemory` parameter or enable temporary key TTL enforcement:
  `CONFIG SET maxmemory 16gb`
- **Tier 3 (Destructive - Requires HITL Sign-Off):**
  Restart caching node or re-shard cluster partition with automated replica promotion.
