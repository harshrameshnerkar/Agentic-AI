# Post-Mortem Incident INC-2026-089: Payment Deadlock Outage

**Date of Incident:** August 14, 2026  
**Duration:** 38 minutes  
**Impact:** Total checkout outage; $185,000 SLA penalty  
**Root Cause:**
A sleep-deprived on-call engineer mistakenly executed `kubectl scale --replicas=0` on the production payments service instead of the staging replica.
Furthermore, un-indexed queries on `order_settlements` locked table rows for 45 seconds, starving connection pools.

**Key Learnings & Action Items:**
1. High-blast destructive operations MUST be blocked behind cryptographic human authorization.
2. SREs need sub-60s automated diagnostic briefs that surface blocking PIDs before any pod restart is considered.
