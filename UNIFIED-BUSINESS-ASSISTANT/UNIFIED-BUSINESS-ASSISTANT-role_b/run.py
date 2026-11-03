"""
Launcher for Role B - Data Service & Interactive Test UI
Runs Role B independently from its own folder:
- Role B API (Groq + Neon PostgreSQL) : http://127.0.0.1:8001 (Docs: /docs)
- Role B Interactive Web UI           : http://127.0.0.1:8501
"""

import os
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Ensure .env is loaded
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass

def main():
    os.chdir(BASE_DIR)
    print("=" * 65)
    print(" STARTING ROLE B DATA SERVICE ONLY")
    print("=" * 65)

    python_exe = sys.executable

    p_api = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "real_api:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=str(BASE_DIR)
    )

    p_ui = subprocess.Popen(
        [python_exe, "role_b_test_ui.py"],
        cwd=str(BASE_DIR)
    )

    print("\nRole B API is running at      : http://127.0.0.1:8001 (Docs: http://127.0.0.1:8001/docs)")
    print("Role B Interactive Web UI at  : http://127.0.0.1:8501")
    print("\nPress Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Role B...")
        p_api.terminate()
        p_ui.terminate()

if __name__ == "__main__":
    main()

