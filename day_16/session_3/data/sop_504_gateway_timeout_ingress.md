# SOP-SRE-307: Ingress Gateway HTTP 504 Timeouts & Upstream Saturation

**Service:** `ingress-nginx`, `envoy-gateway`, `edge-router`  
**Severity:** Sev-1  
**Last Updated:** August 15, 2026  
**Status:** ACTIVE / VERIFIED  
**Owner:** Network & Edge Infrastructure  

---

## 1. Symptoms & Diagnostic Triggers
- Client requests fail with `504 Gateway Time-out` at edge endpoints.
- Edge ingress error logs: `upstream timed out (110: Connection timed out) while reading response header from upstream`.
- Ingress response latency p99 exceeds 15,000ms.

## 2. Immediate Diagnostic Steps
1. Verify whether the timeout is isolated to a specific route or affecting all edge traffic.
2. Check upstream target health:
   `kubectl get endpoints <service-name> -n prod-core`
3. Check ingress controller CPU & socket descriptor limits.

## 3. Recommended Remediation Plan
- **Tier 1 (Read-Only):** Trace which upstream microservice is dropping SYN packets or failing health checks.
- **Tier 2 (Low Risk):** If ingress pod CPU is saturated, scale ingress controller replicas:
  `kubectl scale deployment/ingress-nginx-controller --replicas=8 -n ingress-system`
- **Tier 3 (Destructive - Requires HITL Sign-Off):**
  If upstream service is completely deadlocked, temporarily shift 100% of traffic to the standby secondary cluster.
