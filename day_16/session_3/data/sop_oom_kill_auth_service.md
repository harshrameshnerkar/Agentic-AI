# SOP-SRE-101: Triage & Remediation for Kubernetes OOMKilled Pods

**Service:** `auth-service`, `api-gateway`, `payment-processor`  
**Severity:** Sev-2 / Sev-1  
**Last Updated:** September 20, 2026  
**Status:** ACTIVE / VERIFIED  
**Owner:** Core Platform Reliability Team  

---

## 1. Symptoms & Diagnostic Triggers
- Pod enters `CrashLoopBackOff` with exit code `137` (`OOMKilled`).
- Prometheus alert: `ContainerMemoryUsageRatio > 0.92` for > 3 minutes.
- Error logs show: `java.lang.OutOfMemoryError: Java heap space` or `Fatal error in V8: FatalProcessOutOfMemory`.

## 2. Immediate Diagnostic Steps
1. Execute `kubectl describe pod <pod-name> -n prod-core` and verify `Last State: Terminated (Reason: OOMKilled, Exit Code: 137)`.
2. Check recent deployment timeline in ArgoCD: was a new container image deployed in the last 60 minutes?
3. Inspect memory limit vs request in pod spec:
   ```yaml
   resources:
     limits:
       memory: "2Gi"
     requests:
       memory: "1Gi"
   ```

## 3. Recommended Remediation Plan
- **Tier 1 (Read-Only):** Verify if memory usage is leaking monotonically across all replicas or isolated to canary pods.
- **Tier 2 (Low Risk):** If traffic spike is temporary, increase replica count by +2 to distribute incoming load:
  `kubectl scale deployment/auth-service --replicas=6 -n prod-core`
- **Tier 3 (Destructive - Requires HITL Sign-Off):** 
  If memory leak was introduced by recent canary commit, initiate automated rollback:
  `kubectl rollout undo deployment/auth-service -n prod-core`
