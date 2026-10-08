# SOP-SRE-204: Database Connection Pool Starvation & Query Deadlock

**Service:** `postgres-primary`, `order-service`, `billing-engine`  
**Severity:** Sev-1  
**Last Updated:** October 2, 2026  
**Status:** ACTIVE / VERIFIED  
**Owner:** Database Operations & Data Platform  

---

## 1. Symptoms & Diagnostic Triggers
- Inbound application requests hang and return HTTP 500 or 504.
- Application log excerpts:
  `HikariPool-1 - Connection is not available, request timed out after 30000ms.`
  `FATAL: remaining connection slots are reserved for non-replication superuser connections.`
- Database metric: `pg_stat_activity` active connections $\ge 98\%$ of `max_connections`.

## 2. Immediate Diagnostic Steps
1. Execute read-only diagnostics on PostgreSQL:
   ```sql
   SELECT pid, now() - query_start AS duration, state, query 
   FROM pg_stat_activity 
   WHERE state != 'idle' 
   ORDER BY duration DESC LIMIT 10;
   ```
2. Check for lock contention:
   ```sql
   SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid,
          blocked_activity.query AS blocked_statement
   FROM  pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
   JOIN pg_catalog.pg_locks blocking_locks 
       ON blocking_locks.locktype = blocked_locks.locktype
       AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
       AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation;
   ```

## 3. Recommended Remediation Plan
- **Tier 1 (Read-Only):** Identify the blocking transaction PID and offending query.
- **Tier 3 (Destructive - Requires HITL Sign-Off):** 
  Terminate the specific hung transaction without restarting the entire database:
  `SELECT pg_terminate_backend(<blocking_pid>);`
  *(NEVER restart the primary database without draining read replicas first).*
