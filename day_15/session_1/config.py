"""
Production Configuration for OpsSentinel Enterprise Capstone (Day 15).
Provides environment-aware configuration with fail-safe defaults.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent
CAPSTONE_ROOT = BASE_DIR.parent
DATA_DIR = CAPSTONE_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class CapstoneConfig(BaseModel):
    # Environment & Service Info
    service_name: str = "OpsSentinel-Enterprise-Agent"
    environment: str = os.getenv("ENVIRONMENT", "production")
    version: str = "2.0.0-capstone"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API Server Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    dashboard_port: int = int(os.getenv("DASHBOARD_PORT", "8501"))

    # Database & Storage
    sqlite_db_path: Path = DATA_DIR / "checkpoints.db"
    audit_log_path: Path = DATA_DIR / "audit_trail.log"
    telemetry_path: Path = DATA_DIR / "telemetry.json"
    golden_suite_path: Path = BASE_DIR / "golden_suite.json"

    # LLM & Generation Configuration
    model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    provider: str = os.getenv("LLM_PROVIDER", "google-genai")
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1024"))

    # Concurrency & Async Engine
    max_concurrent_tools: int = int(os.getenv("MAX_CONCURRENT_TOOLS", "5"))
    tool_timeout_seconds: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "10.0"))
    max_agent_steps: int = int(os.getenv("MAX_AGENT_STEPS", "8"))

    # Blast Radius & HITL Gate
    require_hitl_for_tier3: bool = True
    approval_token_expiry_seconds: int = 1800  # 30 minutes
    auto_abort_stale_approvals: bool = True

    # CI Regression Thresholds
    min_ci_pass_rate: float = 0.90  # 90% pass rate required
    max_ci_critical_regressions: int = 0
    max_ci_p95_latency_ms: float = 3000.0

    # Economics & Pricing (per 1k tokens)
    input_cost_per_1k: float = 0.000075
    output_cost_per_1k: float = 0.000300

config = CapstoneConfig()
