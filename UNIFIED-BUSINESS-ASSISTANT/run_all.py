"""
Unified System Launcher (Role A + Role B + Role C)
Starts all three microservices together:
- Role A: Knowledge Service (http://127.0.0.1:8000)
- Role B: Data Service      (http://127.0.0.1:8001)
- Role C: Orchestrator UI   (http://127.0.0.1:8002)

Handles graceful shutdown of all processes on Ctrl+C.
"""

import os
import sys
import time
import subprocess
import signal 
import urllib.request

SERVICES = [
    {
        "name": "Role A - Knowledge Service",
        "cmd": [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        "url": "http://127.0.0.1:8000",
        "health_endpoint": "http://127.0.0.1:8000/health",
        "port": 8000
    },
    {
        "name": "Role B - Data Service",
        "cmd": [sys.executable, "-m", "uvicorn", "app_role_b:app", "--host", "127.0.0.1", "--port", "8001"],
        "url": "http://127.0.0.1:8001",
        "health_endpoint": "http://127.0.0.1:8001/health",
        "port": 8001
    },
    {
        "name": "Role C - Orchestrator & UI",
        "cmd": [sys.executable, "-m", "uvicorn", "app_role_c:app", "--host", "127.0.0.1", "--port", "8002"],
        "url": "http://127.0.0.1:8002",
        "health_endpoint": "http://127.0.0.1:8002/api/contract",
        "port": 8002
    }
]


def check_health(url: str, timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "System-Launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 307)
    except Exception:
        return False


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=" * 70)
    print(" UNIFIED BUSINESS ASSISTANT - STARTING ALL SERVICES")
    print("=" * 70)

    processes = []

    try:
        for svc in SERVICES:
            print(f"\n[+] Launching {svc['name']} on port {svc['port']}...")
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            # Explicitly set PREFER_MOCK=false so Role C queries live services
            env["PREFER_MOCK"] = "false"

            p = subprocess.Popen(
                svc["cmd"],
                cwd=base_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            processes.append((svc, p))

        # Wait for all services to come online
        print("\n[*] Waiting for services to become healthy...")
        for svc, _ in processes:
            ready = False
            for attempt in range(25):
                if check_health(svc["health_endpoint"]):
                    print(f"  [OK] {svc['name']} is UP -> {svc['url']}")
                    ready = True
                    break
                time.sleep(0.8)
            if not ready:
                print(f"  [!] {svc['name']} is still initializing at {svc['url']} (will continue)...")

        print("\n" + "=" * 70)
        print(" ALL SERVICES ARE RUNNING!")
        print("=" * 70)
        print("  Role A (Knowledge Service) : http://127.0.0.1:8000 (Docs: /docs)")
        print("  Role B (Data Service)      : http://127.0.0.1:8001 (Docs: /docs)")
        print("  Role C (Main Orchestrator) : http://127.0.0.1:8002 (Web Dashboard)")
        print("=" * 70)
        print("\nPress Ctrl+C to stop all services.\n")

        # Stream output from all processes
        while True:
            all_alive = False
            for svc, p in processes:
                if p.poll() is None:
                    all_alive = True
                    # Read non-blocking output if available
                    while True:
                        line = p.stdout.readline()
                        if line:
                            print(f"[{svc['name'][:6]}] {line.strip()}")
                        else:
                            break
                else:
                    ret = p.poll()
                    print(f"\n[!] {svc['name']} exited with code {ret}")
            if not all_alive:
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Received shutdown signal (Ctrl+C). Terminating all services...")
    finally:
        for svc, p in processes:
            if p.poll() is None:
                print(f"[*] Stopping {svc['name']} (PID: {p.pid})...")
                try:
                    p.terminate()
                    p.wait(timeout=3)
                except Exception:
                    p.kill()
        print("[*] All services stopped cleanly.")


if __name__ == "__main__":
    main()
