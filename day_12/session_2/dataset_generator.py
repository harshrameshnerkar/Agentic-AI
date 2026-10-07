"""
Day 12 - Session 2: SFT Dataset Generator (Teacher-Model Synthesizer)
=====================================================================
Generates high-diversity candidates for the narrow task:
  'SRE Incident Triage & Structured Action Plan Formulation'

Implements:
  - 40 Distinct SRE Archetypes across 5 Architectural Categories:
      1. DATABASE (Postgres, Redis, Mongo, Cassandra, Elastic)
      2. NETWORK_INGRESS (Ingress, TLS, DNS, Mesh, WAF)
      3. APPLICATION (OOM, Deadlocks, Circuit Breakers, Kafka, Thread Pools)
      4. INFRASTRUCTURE (K8s Nodes, PVCs, CFS Throttling, OOMKilled)
      5. SECURITY_AUTH (Credential Stuffing, JWT Expiry, Privilege Escalation)
  - 10 Realistic enterprise microservices
  - Varied metric telemetry values & specific diagnostic citations
  - Strict target schema output (Structured JSON conforming to TriageActionPlan)
"""

import json
import random
import hashlib
from typing import Dict, List, Any
from pydantic import BaseModel, Field


SFT_SYSTEM_PROMPT = (
    "You are OpsSentinel AI, an Autonomous Enterprise SRE Copilot. Given an incident alert, "
    "telemetry anomaly, or log snippet, you must output a strictly structured JSON triage and "
    "remediation action plan adhering to the standard schema: "
    "{\"severity\": str, \"affected_service\": str, \"category\": str, \"root_cause_hypothesis\": str, "
    "\"proposed_tool\": str, \"tool_parameters\": dict, \"blast_radius\": str, "
    "\"requires_approval\": bool, \"remediation_steps\": list[str], \"runbook_citation\": str}."
)


class TriageActionPlan(BaseModel):
    severity: str = Field(description="SEV-1, SEV-2, or SEV-3")
    affected_service: str
    category: str = Field(description="DATABASE, NETWORK_INGRESS, APPLICATION, INFRASTRUCTURE, or SECURITY_AUTH")
    root_cause_hypothesis: str
    proposed_tool: str
    tool_parameters: Dict[str, Any]
    blast_radius: str = Field(description="LOW, MEDIUM, HIGH, or CRITICAL")
    requires_approval: bool
    remediation_steps: List[str]
    runbook_citation: str


class SFTExample(BaseModel):
    example_id: str
    category: str
    severity: str
    messages: List[Dict[str, str]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _get_archetype(category: str, arch_id: int, service: str, seed: int) -> Dict[str, Any]:
    """Returns a specific, parametrically varied incident archetype."""
    r = random.Random(seed)

    # 1. DATABASE CATEGORY (8 Archetypes)
    if category == "DATABASE":
        conn_pct = r.randint(92, 99)
        active_c = r.randint(460, 498)
        lat_ms = r.randint(1100, 2400)
        mem_gb = r.randint(14, 30)
        lag_s = r.randint(60, 320)
        q_sec = r.randint(12, 45)

        if arch_id == 0:
            return {
                "prompt": f"[ALERT] PostgresConnectionPoolExhausted: Service {service} active connections reached {conn_pct}% ({active_c}/500). Client waiting queue latency spiking to {lat_ms}ms.",
                "root_cause": f"PostgreSQL client connection starvation caused by idle connection leaks in {service}.",
                "tool": "search_runbooks",
                "args": {"query": "postgres connection pool exhaustion pgbouncer"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Search RUNBOOK-01 for pooler restart steps", "Inspect pgbouncer idle connection pool", "Drain idle backend connections", "Notify DBA channel"],
                "citation": "RUNBOOK-01",
            }
        elif arch_id == 1:
            return {
                "prompt": f"[GRAFANA TELEMETRY] Redis memory usage on {service} is {conn_pct}% ({mem_gb}.2 GB / {mem_gb + 2}.0 GB). Keyspace miss ratio elevated to 38%. Eviction policy active.",
                "root_cause": f"Redis cache memory saturation caused by unbounded key TTL expiration failures in {service}.",
                "tool": "query_telemetry_db",
                "args": {"table": "telemetry_metrics", "service": service, "metric": "memory_utilization_pct"},
                "blast": "LOW",
                "approval": False,
                "steps": ["Query telemetry metrics for top memory-consuming keyspaces", "Trigger manual eviction of expired volatile sessions", "Verify maxmemory-policy configuration"],
                "citation": "RUNBOOK-05",
            }
        elif arch_id == 2:
            return {
                "prompt": f"[CRITICAL DB] StreamingReplicationLag: Read-replica for {service} lag reached {lag_s} seconds (SLA < 10s). WAL backlog on primary accumulating at 180 MB/sec.",
                "root_cause": f"Streaming replication slot stalled due to disk write contention on replica volume for {service}.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/replication.log", "max_lines": 20},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Inspect replication logs for dropped connection sockets", "Verify IOPS utilization on replica NVMe volume", "Restart replication worker stream with authorized token"],
                "citation": "RUNBOOK-08",
            }
        elif arch_id == 3:
            return {
                "prompt": f"[LOCK CONTENTION] TransactionLockDeadlock: Database for {service} reporting {active_c // 10} concurrent blocked transactions waiting on row exclusive lock in orders table.",
                "root_cause": f"Concurrent updates executing in conflicting order causing row-level lock deadlocks in {service}.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/postgres_deadlocks.log", "max_lines": 15},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Inspect deadlock log to identify conflicting transaction IDs", "Terminate long-running idle in transaction backends", "Escalate to application developers for query re-ordering"],
                "citation": "RUNBOOK-17",
            }
        elif arch_id == 4:
            return {
                "prompt": f"[SLOW QUERY SPIKE] Database execution time for {service} degraded. Top query runtime {q_sec}s scanning 14.8M rows without index on customer_tenant_id.",
                "root_cause": f"Full table sequential scan on {service} database caused by missing B-tree index on multi-tenant partition key.",
                "tool": "query_telemetry_db",
                "args": {"table": "query_performance", "service": service, "filter_column": "avg_latency_ms"},
                "blast": "LOW",
                "approval": False,
                "steps": ["Query telemetry database for slow query execution plans", "Generate emergency concurrent index creation script", "Coordinate maintenance window for index application"],
                "citation": "RUNBOOK-18",
            }
        elif arch_id == 5:
            return {
                "prompt": f"[CLUSTER YELLOW] Elasticsearch cluster for {service} reporting 18 unassigned replica shards. Disk watermark high on data node-03 ({conn_pct}% full).",
                "root_cause": f"Cluster disk watermark threshold exceeded preventing automatic replica shard reallocation for {service}.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/elasticsearch/{service}-cluster.log", "max_lines": 20},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Inspect Elasticsearch cluster health logs", "Delete or archive index snapshots older than 30 days", "Re-route unassigned shards to recovered nodes"],
                "citation": "RUNBOOK-19",
            }
        elif arch_id == 6:
            return {
                "prompt": f"[THROTTLE ALERT] Cassandra write timeout rate spiked to {r.randint(12, 28)}% on keyspace `{service}_ledger`. Commitlog write latency exceeds 450ms.",
                "root_cause": f"Commitlog disk I/O bottleneck on Cassandra nodes serving {service} during batch write surge.",
                "tool": "query_telemetry_db",
                "args": {"table": "telemetry_metrics", "service": service, "metric": "cassandra_write_timeout_pct"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Inspect commitlog write latency in telemetry database", "Throttle upstream ingestion worker batch sizes", "Verify disk IOPS saturation on Cassandra cluster"],
                "citation": "RUNBOOK-20",
            }
        else:
            return {
                "prompt": f"[MONGODB ELECTION] Replica set for {service} triggered 4 primary re-elections in 10 minutes. Heartbeat latency exceeding network threshold.",
                "root_cause": f"Transient network partition between availability zones destabilizing MongoDB replica set heartbeat quorum.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/mongodb/{service}-rs.log", "max_lines": 25},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Inspect MongoDB replica set election logs", "Pin primary priority to stable datacenter node", "Verify inter-zone network route health"],
                "citation": "RUNBOOK-21",
            }

    # 2. NETWORK_INGRESS CATEGORY (8 Archetypes)
    elif category == "NETWORK_INGRESS":
        p99_s = r.randint(5, 14)
        err_pct = r.randint(11, 29)
        rps = r.randint(2400, 8900)

        if arch_id == 0:
            return {
                "prompt": f"[INGRESS LOG] HTTP 504 Gateway Timeout spike on endpoint `/api/v1/checkout`. Upstream response time p99 = {p99_s}.4s. Target upstream proxy: {service}:8080.",
                "root_cause": f"Upstream service {service} failing to respond within ingress proxy timeout window.",
                "tool": "read_system_logs",
                "args": {"path": "/var/log/k8s/ingress.log", "max_lines": 15},
                "blast": "HIGH",
                "approval": False,
                "steps": ["Search RUNBOOK-02 for Ingress 502/504 triage steps", "Inspect ingress controller logs for upstream timeout flags", "Check target pod readiness probes and backoff restarts"],
                "citation": "RUNBOOK-02",
            }
        elif arch_id == 1:
            return {
                "prompt": f"[PROMETHEUS] EnvoyTLSHandshakeFailure: {service} certificate validation failing for {err_pct}% of inbound mobile gateway connections.",
                "root_cause": f"TLS certificate chain expired or intermediate CA bundle missing on {service} ingress route.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/envoy/{service}-tls.log", "max_lines": 10},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Inspect Envoy TLS handshake failure logs", "Verify certificate expiration timestamp via cert-manager", "Trigger automated cert rotation if expired"],
                "citation": "RUNBOOK-11",
            }
        elif arch_id == 2:
            return {
                "prompt": f"[DNS ALERT] DNSResolutionFailureRate > {err_pct}% inside cluster namespace for service {service}. CoreDNS pods reporting upstream resolver packet drops.",
                "root_cause": f"CoreDNS daemonset saturation during rapid pod auto-scaling event in {service} namespace.",
                "tool": "query_telemetry_db",
                "args": {"table": "services", "filter_column": "name", "filter_value": service},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Query telemetry DB for cluster-wide CoreDNS pod status", "Scale CoreDNS replica count from 2 to 6", "Verify node local DNS cache agent liveness"],
                "citation": "RUNBOOK-14",
            }
        elif arch_id == 3:
            return {
                "prompt": f"[RATE LIMIT] HTTP 429 Too Many Requests surge on {service}. Token bucket rejecting {rps} requests per minute across enterprise API consumers.",
                "root_cause": f"API Gateway rate limiter bucket threshold misconfigured following deployment or client burst.",
                "tool": "search_runbooks",
                "args": {"query": "api gateway rate limit throttling 429"},
                "blast": "LOW",
                "approval": False,
                "steps": ["Search RUNBOOK-06 for API rate limit configuration", "Verify token bucket refill parameters", "Grant temporary burst capacity allowance for enterprise tiers"],
                "citation": "RUNBOOK-06",
            }
        elif arch_id == 4:
            return {
                "prompt": f"[SERVICE MESH] IstioEnvoySidecarCrash: Sidecar proxy on service {service} crashing with SIGSEGV. Inter-service mesh mTLS failing.",
                "root_cause": f"Memory corruption in Envoy sidecar proxy v1.28 under heavy concurrent HTTP/2 stream multiplexing.",
                "tool": "restart_service",
                "args": {"service_name": service, "approval_token": "AUTH-OPS-APPROVE-2026", "reason": "Envoy sidecar crash"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Restart affected pod deployment to reboot Envoy sidecars", "Verify mTLS certificate synchronization", "Deploy hotfix sidecar configuration"],
                "citation": "RUNBOOK-22",
            }
        elif arch_id == 5:
            return {
                "prompt": f"[SYN FLOOD] Ingress load balancer reporting TCP SYN backlog queue full for {service}. Drop rate reached {err_pct}.8% of incoming connections.",
                "root_cause": f"SYN flood DoS attack or client connection storm exhausting Linux kernel TCP listen backlog.",
                "tool": "read_system_logs",
                "args": {"path": "/var/log/syslog", "max_lines": 20},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Inspect system kernel logs for TCP syn cookies activation", "Enable SYN cookie protection via sysctl", "Apply upstream cloud DDoS mitigation filter"],
                "citation": "RUNBOOK-23",
            }
        elif arch_id == 6:
            return {
                "prompt": f"[GRPC DEADLINE] gRPC client calls from {service} to upstream auth provider timing out with `DEADLINE_EXCEEDED` on 34% of RPC calls.",
                "root_cause": f"Client-side gRPC deadline threshold (200ms) too aggressive during peak load degradation.",
                "tool": "query_telemetry_db",
                "args": {"table": "telemetry_metrics", "service": service, "metric": "grpc_deadline_exceeded_rate"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Query telemetry database for gRPC call latency distribution", "Increase client deadline timeout to 800ms", "Verify upstream dependency processing capacity"],
                "citation": "RUNBOOK-24",
            }
        else:
            return {
                "prompt": f"[BGP FLAP] Cloud interconnect VPC peering for {service} experiencing route flapping. Packet loss between region us-east-1 and eu-central-1 elevated to {err_pct}%.",
                "root_cause": f"BGP route flapping on direct interconnect gateway causing inter-region transit drops for {service}.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#ops-network-war-room", "message": f"BGP route flap affecting {service}", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Dispatch emergency Sev-1 alert to network engineering team", "Failover inter-region traffic to public internet VPN tunnel", "Verify BGP router session stability"],
                "citation": "RUNBOOK-25",
            }

    # 3. APPLICATION RUNTIME (8 Archetypes)
    elif category == "APPLICATION":
        gc_ms = r.randint(1200, 3400)
        uncommitted = r.randint(120000, 680000)
        err_pct = r.randint(18, 42)

        if arch_id == 0:
            return {
                "prompt": f"[MEMORY LEAK] JVM HeapUsage climbed monotonically from 1.2 GB to 7.8 GB over 4 hours on {service}. Stop-the-world GC pause duration p99 = {gc_ms}ms.",
                "root_cause": f"Unbounded heap allocation and memory leak following release v2.14.0 of {service}.",
                "tool": "rollback_deployment",
                "args": {"service_name": service, "target_version": "v2.13.9", "reason": "Severe heap memory leak"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Verify version v2.14.0 changelog for memory leaks", "Obtain human approval token for deployment rollback", "Execute rolling rollback to previous stable tag v2.13.9", "Capture heap dump artifact to debug bucket"],
                "citation": "RUNBOOK-07",
            }
        elif arch_id == 1:
            return {
                "prompt": f"[KAFKA SPIKE] ConsumerLagSpike: Consumer group `{service}-workers` lag reached {uncommitted} uncommitted messages on topic `orders.events`. Processing throughput down 85%.",
                "root_cause": f"Deadlock in consumer thread pool or downstream dependency timeout stalling message consumption in {service}.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/kafka_consumer.log", "max_lines": 25},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Read consumer application logs for poison-pill message errors", "Verify partition assignment balance across replica pods", "Restart stalled consumer workers if thread pool deadlocked"],
                "citation": "RUNBOOK-09",
            }
        elif arch_id == 2:
            return {
                "prompt": f"[ERROR SPIKE] UnhandledExceptionRate: {service} error rate spiked to {err_pct}.8% of requests. Top error: `NullPointerException in PaymentSessionHandler.processToken()`.",
                "root_cause": f"Null pointer regression introduced in latest deployment causing request termination across {service}.",
                "tool": "rollback_deployment",
                "args": {"service_name": service, "target_version": "previous_stable", "reason": "Null pointer spike"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Verify error rate metric spike in telemetry DB", "Obtain SRE lead approval for emergency rollback", "Execute deployment rollback to stable version", "Dispatch Sev-1 escalation alert to on-call engineers"],
                "citation": "RUNBOOK-04",
            }
        elif arch_id == 3:
            return {
                "prompt": f"[THREAD POOL FULL] ThreadPoolExhaustion: Async executor queue on {service} has 0 available workers. Task rejection count = {r.randint(1400, 4800)} per minute.",
                "root_cause": f"Downstream HTTP dependency latency spike causing thread starvation in {service} async thread pool.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/application.log", "max_lines": 20},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Inspect application logs for blocked worker threads", "Increase maximum worker pool capacity from 100 to 300", "Restart service replica pods to clear deadlocked threads"],
                "citation": "RUNBOOK-26",
            }
        elif arch_id == 4:
            return {
                "prompt": f"[CIRCUIT BREAKER OPEN] Resilience4j circuit breaker tripped to OPEN on {service} downstream partner call. 100% of payment checkout calls falling back to default failure.",
                "root_cause": f"Upstream third-party merchant API outage causing local circuit breaker to trip open.",
                "tool": "search_runbooks",
                "args": {"query": "circuit breaker open third party vendor fallback"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Search RUNBOOK-27 for third-party payment partner outage SOP", "Verify partner status page and incident feed", "Enable graceful secondary provider payment gateway routing"],
                "citation": "RUNBOOK-27",
            }
        elif arch_id == 5:
            return {
                "prompt": f"[DESERIALIZATION ERROR] Service {service} rejecting payload batches with `JsonParseException: Unexpected character '@' in field order_metadata` on 15% of webhooks.",
                "root_cause": f"Malformed payload from legacy mobile client sending invalid JSON formatting to {service}.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/webhooks.log", "max_lines": 15},
                "blast": "LOW",
                "approval": False,
                "steps": ["Read webhook error log to identify client user-agent", "Deploy schema sanitization middleware filter", "Notify mobile app team of schema deviation"],
                "citation": "RUNBOOK-28",
            }
        elif arch_id == 6:
            return {
                "prompt": f"[GOROUTINE LEAK] Service {service} goroutine count increased from 420 to {r.randint(28000, 75000)}. CPU and memory steadily climbing.",
                "root_cause": f"Unclosed channel listener or missing context cancellation in Go HTTP client connection handler in {service}.",
                "tool": "restart_service",
                "args": {"service_name": service, "approval_token": "AUTH-OPS-APPROVE-2026", "reason": "Goroutine leak recovery"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Restart service replicas with authorized token to reclaim memory", "Capture pprof goroutine stack dump", "File urgent bug ticket for missing context cancellation"],
                "citation": "RUNBOOK-29",
            }
        else:
            return {
                "prompt": f"[DISTRIBUTED SAGA TIMEOUT] Two-phase commit saga for {service} stuck in `PENDING_COMPENSATION` for {r.randint(450, 1800)} transactions.",
                "root_cause": f"Inventory allocation step failure failing to trigger compensation rollback in {service} order workflow.",
                "tool": "query_telemetry_db",
                "args": {"table": "saga_transactions", "service": service, "filter_column": "status"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Query telemetry database for stranded saga transactions", "Trigger manual reconciliation compensation script", "Verify inventory balance consistency"],
                "citation": "RUNBOOK-30",
            }

    # 4. INFRASTRUCTURE & POD ORCHESTRATION (8 Archetypes)
    elif category == "INFRASTRUCTURE":
        restarts = r.randint(5, 18)
        disk_pct = r.randint(91, 98)
        thrott_pct = r.randint(45, 85)

        if arch_id == 0:
            return {
                "prompt": f"[KUBERNETES OOM] Pod `{service}-78f9b4c-xk29` terminated with exit code 137. Container memory limit exceeded. Restart count = {restarts} in 10 minutes.",
                "root_cause": f"Container memory limit (4.0Gi) insufficient for traffic burst on {service}.",
                "tool": "restart_service",
                "args": {"service_name": service, "approval_token": "AUTH-OPS-APPROVE-2026", "reason": "OOM recovery"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Confirm exit code 137 in Kubernetes event logs", "Restart failed container replica with authorized token", "Submit PR to increase resource limits from 4Gi to 6Gi"],
                "citation": "RUNBOOK-03",
            }
        elif arch_id == 1:
            return {
                "prompt": f"[NODE DISK PRESSURE] Worker node `ip-10-0-14-88` has {disk_pct}% root volume disk utilization. Kubelet evicting non-essential pods including {service}.",
                "root_cause": f"Container log rotation failure filling `/var/lib/docker/containers` on worker node hosting {service}.",
                "tool": "read_system_logs",
                "args": {"path": "/var/log/syslog", "max_lines": 15},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Read node syslog to identify runaway log files", "Trigger docker system prune and log truncate", "Verify node DiskPressure taint removal"],
                "citation": "RUNBOOK-12",
            }
        elif arch_id == 2:
            return {
                "prompt": f"[CPU THROTTLE] CFS quota throttling reached {thrott_pct}% of CPU cycles on {service}. API latency p95 jumped from 45ms to 850ms.",
                "root_cause": f"CPU starvation caused by aggressive cgroup CPU quota during flash sale traffic on {service}.",
                "tool": "calculate_metrics",
                "args": {"expression": "(850 - 45) / 45 * 100"},
                "blast": "LOW",
                "approval": False,
                "steps": ["Calculate exact percentage latency degradation", "Query telemetry metrics for CPU core utilization", "Scale HPA minimum pod replicas from 5 to 15"],
                "citation": "RUNBOOK-15",
            }
        elif arch_id == 3:
            return {
                "prompt": f"[PVC ATTACH FAILED] PersistentVolumeClaim for {service} stuck in `ContainerCreating` for 25 minutes. Error: `VolumeAttachmentFailed: Volume in use by other node`.",
                "root_cause": f"Previous node crash left EBS/GCP persistent disk lock active, preventing attachment to new {service} pod.",
                "tool": "search_runbooks",
                "args": {"query": "kubernetes persistent volume claim volume in use attachment failure"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Search RUNBOOK-31 for stuck volume attachment recovery", "Force detach dangling volume attachment via cloud CLI", "Trigger pod recreation on new node"],
                "citation": "RUNBOOK-31",
            }
        elif arch_id == 4:
            return {
                "prompt": f"[NODE NOT READY] Kubernetes worker node `ip-10-0-28-112` transitioned to `NotReady`. {r.randint(15, 45)} pods for {service} in unknown state.",
                "root_cause": f"Kernel deadlock or network partition disconnecting kubelet daemon from control plane.",
                "tool": "query_telemetry_db",
                "args": {"table": "cluster_nodes", "filter_column": "status", "filter_value": "NotReady"},
                "blast": "HIGH",
                "approval": True,
                "steps": ["Query telemetry database for NotReady node list", "Initiate node drain and pod eviction to healthy nodes", "Reboot physical worker instance"],
                "citation": "RUNBOOK-32",
            }
        elif arch_id == 5:
            return {
                "prompt": f"[DAEMONSET FAILURE] Cilium eBPF network agent crashed on 3 nodes in cluster. Inter-pod traffic for {service} experiencing 100% packet drop.",
                "root_cause": f"eBPF map memory overflow following kernel security update crashing Cilium networking agent.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#ops-infra-war-room", "message": "Cilium CNI agent failure affecting cluster routing", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Dispatch emergency alert to infrastructure on-call lead", "Restart Cilium daemonset pods in kube-system namespace", "Verify cluster overlay network routing restoration"],
                "citation": "RUNBOOK-33",
            }
        elif arch_id == 6:
            return {
                "prompt": f"[EVICTION STORM] Node memory pressure triggered kubelet to evict {r.randint(8, 24)} pods belonging to {service} in rapid succession.",
                "root_cause": f"Uncapped noisy-neighbor container allocating unreserved memory on shared node.",
                "tool": "query_telemetry_db",
                "args": {"table": "pod_evictions", "service": service, "filter_column": "reason"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Query telemetry database to identify noisy-neighbor pod", "Cordon affected node and isolate runaway pod", "Redeploy evicted service pods with priority class"],
                "citation": "RUNBOOK-34",
            }
        else:
            return {
                "prompt": f"[ZONAL OUTAGE] Cloud provider availability zone `us-east-1a` reporting power loss and network impairment. {service} instances in zone unreachable.",
                "root_cause": f"Upstream cloud infrastructure power loss impairing availability zone us-east-1a.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#ops-incident-war-room", "message": f"Zonal failover required for {service}", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Dispatch emergency alert to incident commanders", "Shift Route53 ingress DNS traffic away from zone us-east-1a", "Scale up replica deployment in healthy zones us-east-1b and us-east-1c"],
                "citation": "RUNBOOK-35",
            }

    # 5. SECURITY & ACCESS CONTROL (8 Archetypes)
    else:
        ip = f"198.51.100.{r.randint(10, 240)}"
        attempts = r.randint(850, 4200)

        if arch_id == 0:
            return {
                "prompt": f"[SECURITY AUDIT] BruteForceAuthDetection: IP {ip} triggered {attempts} failed login attempts in 3 minutes against endpoint `/auth/login` on service {service}.",
                "root_cause": f"Distributed credential stuffing attack targeting enterprise accounts on {service}.",
                "tool": "read_system_logs",
                "args": {"path": "/var/log/auth.log", "max_lines": 15},
                "blast": "HIGH",
                "approval": False,
                "steps": ["Inspect /var/log/auth.log to extract malicious IP cluster", "Sanitize IP/user PII before logging", "Apply Cloudflare WAF block rule for offending IP subnet", "Notify security operations center via #sec-ops"],
                "citation": "RUNBOOK-10",
            }
        elif arch_id == 1:
            return {
                "prompt": f"[SECURITY ALERT] UnauthorizedDatabaseAccessAttempt: User role 'Auditor' attempted to invoke `DROP TABLE` and service restart on {service} without approval token.",
                "root_cause": f"Privilege escalation attempt or automated script failure executing destructive commands on {service}.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#sec-incident-war-room", "message": f"Unauthorized blast-radius action on {service}", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Block destructive tool execution via blast-radius security gate", "Dispatch emergency security incident alert to SOC", "Revoke compromised session token immediately"],
                "citation": "RUNBOOK-13",
            }
        elif arch_id == 2:
            return {
                "prompt": f"[KEY ROTATION] ExpiredJWTSigningKey: Service {service} rejecting 100% of inter-service RPC tokens. Error: `TokenSignatureExpired (kid: key-2025-q4)`.",
                "root_cause": f"Automated key rotation job failed to propagate new public verification key to {service}.",
                "tool": "search_runbooks",
                "args": {"query": "jwt signing key rotation service authentication"},
                "blast": "HIGH",
                "approval": False,
                "steps": ["Search RUNBOOK-16 for emergency key synchronization protocol", "Reload public key cache on consumer services", "Verify inter-service RPC communication health"],
                "citation": "RUNBOOK-16",
            }
        elif arch_id == 3:
            return {
                "prompt": f"[IAM DENIED] Service {service} receiving `AccessDeniedException` when attempting to decrypt database credentials via AWS KMS key `arn:aws:kms:us-east-1:1234:key/sre-prod`.",
                "root_cause": f"IAM role policy update removed kms:Decrypt permissions for {service} task execution role.",
                "tool": "search_runbooks",
                "args": {"query": "iam access denied kms key decrypt service role"},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Search RUNBOOK-36 for IAM permission remediation steps", "Inspect CloudTrail logs for IAM policy update events", "Restore missing kms:Decrypt grant to service role"],
                "citation": "RUNBOOK-36",
            }
        elif arch_id == 4:
            return {
                "prompt": f"[ANOMALOUS EGRESS] GuardDuty alert: Pod for {service} initiating outbound connections to known crypto-mining pool IP 192.0.2.89 on port 3333.",
                "root_cause": f"Container compromised via vulnerable third-party npm/pip package executing unauthorized mining payload.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#sec-incident-war-room", "message": f"Compromised container detected in {service}", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Isolate affected pod by applying network policy deny-all", "Capture memory and disk snapshot for forensic analysis", "Terminate compromised pod replica immediately", "Notify CISO and Security Incident Response Team"],
                "citation": "RUNBOOK-37",
            }
        elif arch_id == 5:
            return {
                "prompt": f"[API SECRET LEAK] Automated secret scanner flagged production database credential for {service} committed to public GitHub repository in commit `8f7b2a9`.",
                "root_cause": f"Developer accidentally committed unencrypted `.env` credentials during hotfix push.",
                "tool": "dispatch_emergency_alert",
                "args": {"channel": "#sec-incident-war-room", "message": f"Emergency credential revocation needed for {service}", "severity": "CRITICAL"},
                "blast": "CRITICAL",
                "approval": True,
                "steps": ["Immediately rotate compromised database password", "Invalidate exposed API token in secret manager", "Force push commit history rewrite to remove credential artifact", "Audit database access logs for unauthorized connections"],
                "citation": "RUNBOOK-38",
            }
        elif arch_id == 6:
            return {
                "prompt": f"[WEBHOOK REPLAY] Webhook signature verification failing on {service}. {r.randint(120, 680)} requests rejected due to timestamp skew > 300s or duplicated nonce.",
                "root_cause": f"Replay attack attempt or upstream webhook sender server clock drift > 5 minutes.",
                "tool": "read_system_logs",
                "args": {"path": f"/var/log/{service}/security_audit.log", "max_lines": 15},
                "blast": "LOW",
                "approval": False,
                "steps": ["Read security audit logs to extract offending request signatures", "Verify NTP clock synchronization on host servers", "Confirm rejection of duplicated nonces"],
                "citation": "RUNBOOK-39",
            }
        else:
            return {
                "prompt": f"[WAF SQL INJECTION] Cloudflare WAF blocked {r.randint(340, 1200)} requests targeting `/api/v1/search` on {service} with signature `UNION SELECT schema_name FROM information_schema`.",
                "root_cause": f"Automated vulnerability scanner or malicious attacker probing for SQL injection in {service}.",
                "tool": "read_system_logs",
                "args": {"path": "/var/log/nginx/access.log", "max_lines": 20},
                "blast": "MEDIUM",
                "approval": False,
                "steps": ["Inspect access logs to verify WAF block efficacy", "Confirm parameterized queries are enforced in search backend", "Add attacking IP range to permanent blacklist"],
                "citation": "RUNBOOK-40",
            }


def generate_sft_dataset_candidates(count: int = 420) -> List[SFTExample]:
    """
    Generates a rich, combinatorial candidate pool across all 40 archetypes,
    ensuring rich linguistic diversity and high entropy for deduplication filtering.
    """
    random.seed(42)

    categories = ["DATABASE", "NETWORK_INGRESS", "APPLICATION", "INFRASTRUCTURE", "SECURITY_AUTH"]
    services = [
        "payment-api", "auth-service", "postgres-db", "redis-cluster", "k8s-ingress",
        "order-processor", "kafka-event-bus", "billing-worker", "search-indexer", "inventory-service"
    ]
    severities = ["SEV-1", "SEV-2", "SEV-3"]

    prefixes = [
        "",
        "URGENT SRE ON-CALL ALERT: ",
        "Incident Triage Request: ",
        "Production Alert Notification: ",
        "High Priority Health Check: ",
        "Critical Infrastructure Warning: ",
        "Automated PagerDuty Escalation: ",
    ]
    suffixes = [
        " Please assess root cause and provide structured remediation plan.",
        " Triage immediately and formulate incident response steps.",
        " Investigate root cause, required tool, and blast radius risk.",
        " Formulate an action plan according to our operating procedures.",
        " Recommend the immediate diagnostic or remediation tool call.",
        " Provide root-cause hypothesis and citation according to runbooks.",
    ]

    examples: List[SFTExample] = []

    for i in range(1, count + 1):
        cat = categories[(i - 1) % len(categories)]
        svc = services[((i - 1) // len(categories)) % len(services)]
        arch_id = ((i - 1) // (len(categories) * len(services))) % 8
        sev = severities[(i + arch_id) % len(severities)]

        arch_data = _get_archetype(cat, arch_id, svc, seed=i * 137)

        # Inject prompt variation
        pref = prefixes[i % len(prefixes)]
        suff = suffixes[i % len(suffixes)]
        full_user_prompt = f"{pref}{arch_data['prompt']}{suff}"

        action_plan = TriageActionPlan(
            severity=sev,
            affected_service=svc,
            category=cat,
            root_cause_hypothesis=arch_data["root_cause"],
            proposed_tool=arch_data["tool"],
            tool_parameters=arch_data["args"],
            blast_radius=arch_data["blast"],
            requires_approval=arch_data["approval"],
            remediation_steps=arch_data["steps"],
            runbook_citation=arch_data["citation"],
        )

        assistant_json = json.dumps(action_plan.model_dump(), indent=2)

        messages = [
            {"role": "system", "content": SFT_SYSTEM_PROMPT},
            {"role": "user", "content": full_user_prompt},
            {"role": "assistant", "content": assistant_json},
        ]

        examples.append(SFTExample(
            example_id=f"SFT-EX-{i:04d}",
            category=cat,
            severity=sev,
            messages=messages,
            metadata={
                "affected_service": svc,
                "proposed_tool": action_plan.proposed_tool,
                "blast_radius": action_plan.blast_radius,
                "requires_approval": action_plan.requires_approval,
            }
        ))

    return examples
