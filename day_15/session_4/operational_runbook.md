# OpsSentinel Enterprise: Operational Runbook & Production Playbook

```text
=============================================================================
Runbook ID:      OPS-RUNBOOK-015
Service:         OpsSentinel Enterprise AI SRE Copilot
Tier:            Tier 1 Mission Critical
On-Call Rotation: sre-core-platform
Incident Channel: #sre-ops-sentinel-alerts
=============================================================================
```

---

## 1. INCIDENT TRIAGE & DETECTION PLAYBOOK

### 1.1 Alert: `SREAgentHighLatencyBreach` (p95 > 3000ms)
- **Symptoms:** Alertmanager fires warning that diagnostic triage latency exceeded 3000ms.
- **Triage Steps:**
  1. Inspect network connectivity to Prometheus / Elasticsearch telemetry endpoints.
  2. Check current concurrent load:
     ```bash
     curl -s http://localhost:8000/api/v1/telemetry | jq .
     ```
  3. If agent event loop is backlogged, increase replica count in Kubernetes:
     ```bash
     kubectl scale deployment/opssentinel-api --replicas=4 -n opssentinel
     ```

### 1.2 Alert: `HITLApprovalQueueBacklog` (Pending > 10 for > 15m)
- **Symptoms:** More than 10 destructive remediations awaiting human SRE authorization.
- **Triage Steps:**
  1. Access the Streamlit Operations Dashboard (`http://<host>:8501`) and navigate to **HITL Approval Gate Queue**.
  2. Or fetch pending requests via CLI:
     ```bash
     curl -s http://localhost:8000/api/v1/hitl/pending | jq .
     ```
  3. Authorize or reject each pending ticket based on service stability.

### 1.3 Alert: `CryptographicAuditTamperDetected`
- **Symptoms:** Cryptographic audit integrity check returned `false`.
- **Immediate Escalation:** P0 Security Incident.
  1. Freeze container filesystem to preserve forensic evidence:
     ```bash
     docker pause opssentinel-api-prod
     ```
  2. Run audit verification probe:
     ```bash
     python day_15/session_1/main.py --audit-check
     ```
  3. Engage Security Operations Center (SOC) on-call lead.

---

## 2. DISASTER RECOVERY & BACKUP/RESTORE

### 2.1 SQLite WAL State Recovery
The agent checkpoints state to `/app/day_15/data/checkpoints.db` using Write-Ahead Logging (`checkpoints.db-wal` and `checkpoints.db-shm`).
- **Taking an Online Backup:**
  ```bash
  sqlite3 day_15/data/checkpoints.db ".backup 'day_15/data/checkpoints_backup.db'"
  ```
- **Restoring from Backup:**
  ```bash
  cp day_15/data/checkpoints_backup.db day_15/data/checkpoints.db
  ```

---

## 3. ZERO-DOWNTIME CONTAINER DEPLOYMENT

```bash
# 1. Build and validate multi-stage production image
docker compose -f day_15/docker-compose.yml build

# 2. Start services in background
docker compose -f day_15/docker-compose.yml up -d

# 3. Verify health probes
curl -f http://localhost:8000/health
```
