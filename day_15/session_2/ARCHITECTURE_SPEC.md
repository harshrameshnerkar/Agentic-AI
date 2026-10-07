# OpsSentinel Enterprise: Subsystem Architecture Specification

## 1. REST API Specification (OpenAPI 3.1 Excerpt)

### 1.1 Agent Execution
- **Endpoint:** `POST /api/v1/agent/run`
- **Request Body:**
  ```json
  {
    "query": "Check metrics, CPU, and 500 error rate for auth-service",
    "session_id": "SES-OPTIONAL",
    "user_id": "sre-oncall-01",
    "tenant_id": "tenant-production"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "session_id": "SES-A1B2C3D4",
    "status": "COMPLETED",
    "query": "Check metrics, CPU, and 500 error rate for auth-service",
    "routing_category": "DIAGNOSTIC_READ",
    "target_service": "auth-service",
    "final_output": "### Comprehensive Infrastructure Diagnostic...",
    "latency_ms": 164.2,
    "total_tokens": 182,
    "estimated_cost": 0.000028,
    "tools_executed": ["fetch_service_metrics", "fetch_cluster_logs", "check_endpoint_health", "get_service_topology"],
    "checkpoints_count": 3
  }
  ```

### 1.2 Human Approval Gate
- **Endpoint:** `POST /api/v1/hitl/approve`
- **Request Body:**
  ```json
  {
    "approval_id": "APV-9F2B1A",
    "operator_id": "sre-senior-lead",
    "rationale": "Verified replica count; authorization granted for rolling restart."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "approval_id": "APV-9F2B1A",
    "session_id": "SES-A1B2C3D4",
    "status": "APPROVED",
    "decision_by": "sre-senior-lead",
    "decision_rationale": "Verified replica count; authorization granted for rolling restart."
  }
  ```

### 1.3 Cryptographic Audit Verification
- **Endpoint:** `GET /api/v1/audit/integrity`
- **Response (200 OK):**
  ```json
  {
    "tamper_evident_integrity": true,
    "chain_algorithm": "SHA-256 forward hash-chain",
    "log_path": "/app/day_15/data/audit_trail.log"
  }
  ```

---

## 2. SQLite Schema & Index Topology

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_step INTEGER NOT NULL DEFAULT 0,
    query TEXT NOT NULL,
    routing_decision_json TEXT,
    accumulated_context_json TEXT,
    pending_approval_id TEXT,
    final_output TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE checkpoints (
    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    state_snapshot_json TEXT NOT NULL,
    checksum_hash TEXT NOT NULL,
    timestamp REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE step_executions (
    execution_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    tier TEXT NOT NULL,
    input_params_json TEXT NOT NULL,
    output_result_json TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    error_msg TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_checkpoints_session ON checkpoints(session_id, step_index);
```
