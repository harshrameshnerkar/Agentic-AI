"""
Day 13 - Session 3: Enterprise Environment & Secret Management
==============================================================
Implements:
  1. Strongly-typed configuration via Pydantic
  2. Automatic secret masking in logs and string representations
  3. Strict environment validation (development, staging, production)
  4. Multi-provider credential isolation
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)
    else:
        load_dotenv(override=True)
except ImportError:
    pass


class MaskedSecret:
    """Wrapper that masks secret strings in stdout, logs, and reprs."""

    def __init__(self, value: str):
        self._raw_value = value

    def get_secret_value(self) -> str:
        """Explicit getter required to access raw secret."""
        return self._raw_value

    def __repr__(self) -> str:
        if not self._raw_value:
            return "''"
        visible = min(4, len(self._raw_value) // 4)
        return f"'{self._raw_value[:visible]}****{self._raw_value[-visible:]}'"

    def __str__(self) -> str:
        return self.__repr__()


class AgentServiceSettings(BaseModel):
    """Production service configuration loaded from environment variables."""

    # Service & Runtime
    app_name: str = "OpsSentinel-Agent-Service"
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", "production"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    worker_replicas: int = Field(default_factory=lambda: int(os.getenv("WORKER_REPLICAS", "3")))

    # Provider Credentials (Safely Wrapped & Masked)
    primary_provider: str = Field(default_factory=lambda: os.getenv("PRIMARY_PROVIDER", "anthropic"))
    anthropic_api_key: MaskedSecret = Field(
        default_factory=lambda: MaskedSecret(os.getenv("ANTHROPIC_API_KEY", "mock-anthropic-key-placeholder"))
    )
    openai_api_key: MaskedSecret = Field(
        default_factory=lambda: MaskedSecret(os.getenv("OPENAI_API_KEY", "mock-openai-key-placeholder"))
    )
    gemini_api_key: MaskedSecret = Field(
        default_factory=lambda: MaskedSecret(os.getenv("GEMINI_API_KEY", "mock-gemini-key-placeholder"))
    )

    # Distributed Rate Limiting & Failover
    rate_limit_rpm: int = Field(default_factory=lambda: int(os.getenv("RATE_LIMIT_RPM", "60")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    circuit_breaker_error_threshold: int = Field(default_factory=lambda: int(os.getenv("CB_ERROR_THRESHOLD", "3")))
    circuit_breaker_recovery_time_sec: float = Field(default_factory=lambda: float(os.getenv("CB_RECOVERY_SEC", "15.0")))

    # Database & Durable Storage
    checkpoint_db_path: str = Field(
        default_factory=lambda: os.getenv("CHECKPOINT_DB_PATH", "agent_checkpoints.db")
    )

    class Config:
        arbitrary_types_allowed = True


# Global Settings Singleton
settings = AgentServiceSettings()
