"""
Authoritative Raw Incident Data, Verbose Logs, and Multi-Metric Telemetry.
Simulates a real-world Kubernetes microservice outage with extensive diagnostic noise.
"""

from typing import Any, Dict, List

# Raw incident metadata with extraneous cluster debugging details
RAW_INCIDENT_PAYLOAD: Dict[str, Any] = {
    "incident_id": "INC-8821",
    "cluster": "k8s-us-east-prod-04",
    "region": "us-east-1",
    "vpc_id": "vpc-09882a17f2231bca0",
    "kubernetes_version": "v1.30.2-eks-128a",
    "control_plane_status": "HEALTHY",
    "etcd_latency_ms": 1.42,
    "cni_plugin": "amazon-vpc-cni-k8s:v1.18.1",
    "kube_proxy_mode": "iptables",
    "service_name": "Auth-Token-Issuer",
    "namespace": "core-services",
    "reported_symptom": "HTTP 500 spike (38.4% error rate) and cascading auth timeouts in Checkout Gateway.",
    "severity": "P1 - CRITICAL",
    "active_pods": 6,
    "desired_pods": 8,
    "node_group": "m6i.4xlarge-spot-fleet-az1",
    "security_groups": ["sg-0a1829bcdef12", "sg-0992384aabc"],
    "internal_routing_tags": {"env": "prod", "tier": "tier-0", "billing_id": "dept-fin-9912", "pci_scope": "true"},
}

# Raw multi-column system telemetry (20+ metrics per sample, mostly normal baseline noise)
RAW_TELEMETRY_SERIES: List[Dict[str, Any]] = [
    {
        "timestamp": "2026-10-06T05:30:00Z",
        "cpu_usage_pct": 34.2,
        "load_avg_1m": 2.1,
        "load_avg_5m": 2.0,
        "memory_rss_mb": 4200,
        "memory_max_mb": 8192,
        "metaspace_used_mb": 245,
        "metaspace_max_mb": 256,  # 95.7% full
        "gc_pause_time_ms": 140,
        "gc_throughput_pct": 98.2,
        "active_threads": 180,
        "socket_handles": 1120,
        "disk_read_kbps": 450,
        "disk_write_kbps": 1200,
        "network_rx_kbps": 8900,
        "network_tx_kbps": 9100,
        "cache_hit_rate": 0.94,
        "kernel_context_switches": 45000,
    },
    {
        "timestamp": "2026-10-06T05:40:00Z",
        "cpu_usage_pct": 88.5,
        "load_avg_1m": 8.4,
        "load_avg_5m": 6.1,
        "memory_rss_mb": 7890,
        "memory_max_mb": 8192,
        "metaspace_used_mb": 255,  # 99.6% SATURATED!
        "metaspace_max_mb": 256,
        "gc_pause_time_ms": 4850,  # 4.85 second Stop-The-World GC freeze!
        "gc_throughput_pct": 32.1,
        "active_threads": 820,
        "socket_handles": 4200,
        "disk_read_kbps": 510,
        "disk_write_kbps": 3400,
        "network_rx_kbps": 12400,
        "network_tx_kbps": 11800,
        "cache_hit_rate": 0.41,
        "kernel_context_switches": 198000,
    },
]

# Raw verbose container logs with 40+ lines of stack trace noise
RAW_CONTAINER_LOGS: str = """
2026-10-06T05:39:58.102Z [INFO]  [org.springframework.boot.StartupInfoLogger] Starting AuthServiceApplication using Java 21 on pod auth-token-issuer-79d8c9bc8-x92zk
2026-10-06T05:40:01.411Z [DEBUG] [io.grpc.netty.NettyServerHandler] [id: 0x48a1290f, L:/10.244.3.42:8080 - R:/10.244.1.18:49212] INBOUND HEADERS: streamId=15 headers=GrpcHttp2RequestHeaders[:path: /auth.TokenService/IssueToken, :authority: auth.prod:8080, :method: POST]
2026-10-06T05:40:01.420Z [DEBUG] [io.grpc.netty.NettyServerHandler] [id: 0x48a1290f] INBOUND DATA: streamId=15 padding=0 endStream=true length=84 bytes=000000004f0a28...
2026-10-06T05:40:02.100Z [INFO]  [com.company.auth.plugin.HotReloadWatcher] Dynamic rule refresh triggered by configmap sync event: hash=9a8bc410
2026-10-06T05:40:02.105Z [INFO]  [com.company.auth.plugin.HotReloadWatcher] Generating dynamic class proxy: TokenValidatorProxy_v4981 via ByteBuddy
2026-10-06T05:40:02.215Z [ERROR] [com.company.auth.plugin.HotReloadWatcher] ClassLoader class definition failed: unable to allocate Metaspace chunk.
java.lang.OutOfMemoryError: Metaspace
	at java.base/java.lang.ClassLoader.defineClass1(Native Method) ~[na:na]
	at java.base/java.lang.ClassLoader.defineClass(ClassLoader.java:1017) ~[na:na]
	at net.bytebuddy.dynamic.loading.ByteArrayClassLoader.findClass(ByteArrayClassLoader.java:402) ~[byte-buddy-1.14.9.jar:1.14.9]
	at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:589) ~[na:na]
	at com.company.auth.plugin.HotReloadWatcher.reloadDynamicClass(HotReloadWatcher.java:142) ~[auth-service.jar:3.4.1]
	at com.company.auth.plugin.HotReloadWatcher.onConfigMapChanged(HotReloadWatcher.java:88) ~[auth-service.jar:3.4.1]
	at com.company.auth.config.K8sConfigWatcher.lambda$poll$2(K8sConfigWatcher.java:64) ~[auth-service.jar:3.4.1]
	at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:572) ~[na:na]
	at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:317) ~[na:na]
	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1144) ~[na:na]
	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:642) ~[na:na]
	at java.base/java.lang.Thread.run(Thread.java:1583) [na:na]
2026-10-06T05:40:03.112Z [FATAL] [org.springframework.boot.SpringApplication] Application run failed due to unrecoverable JVM error
java.lang.OutOfMemoryError: Metaspace
	at java.base/java.lang.ClassLoader.defineClass1(Native Method) ~[na:na]
2026-10-06T05:40:03.890Z [WARN]  [io.netty.channel.DefaultChannelPipeline] An exceptionCaught() event was fired, and it reached at the tail of the pipeline. It resulted in a ForceClose.
io.netty.handler.codec.DecoderException: java.lang.OutOfMemoryError: Metaspace
2026-10-06T05:40:04.100Z [INFO]  [k8s.kubelet] Liveness probe failed for container "auth-service" in pod "auth-token-issuer-79d8c9bc8-x92zk": HTTP probe failed with statuscode: 503
"""

# Ground truth expected findings for evaluation
GROUND_TRUTH_FINDINGS = {
    "incident_id": "INC-8821",
    "affected_service": "Auth-Token-Issuer",
    "root_cause_exception": "java.lang.OutOfMemoryError: Metaspace",
    "culprit_component": "HotReloadWatcher",
    "trigger_mechanism": "Dynamic ByteBuddy class proxy generation on configmap reload exhausting 256MB Metaspace limit",
    "critical_telemetry": "Metaspace saturated at 99.6% (255MB/256MB) triggering 4.85s Stop-The-World GC pause",
    "remediation": "Disable dynamic ByteBuddy class generation on config reload or increase MaxMetaspaceSize with proper ClassLoader recycling.",
}
