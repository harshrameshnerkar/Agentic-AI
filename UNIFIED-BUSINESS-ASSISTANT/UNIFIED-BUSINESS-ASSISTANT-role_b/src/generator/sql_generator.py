"""
Groq-backed SQL Generation Module for Role B Data Service.
Generates safe, bounded SQLite queries from natural language business questions.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any

# pyrefly: ignore[missing-import]
import groq
from groq import GroqError

from src.database.connection import get_project_root
from src.generator.prompts import NORTHWIND_SCHEMA_PROMPT
from src.safety.validator import (
    DEFAULT_ROW_LIMIT,
    MAX_ROW_LIMIT,
    SQLSafetyValidator,
    SQLValidationError,
)


DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


class SQLGenerationError(Exception):
    """Base exception for SQL generation failures."""


class GroqConfigurationError(SQLGenerationError):
    """Raised when required Groq credentials or configuration are missing."""


class GroqProviderError(SQLGenerationError):
    """Raised when Groq API communication, authentication, or rate limits fail."""


@dataclass(frozen=True)
class GenerationResult:
    """Encapsulates generated and validated SQL query results."""

    question: str
    raw_response: str
    sql: str
    model: str
    tables_referenced: list[str]


def load_env_file(dotenv_path: Path | None = None) -> None:
    """Load .env values without overriding existing environment variables."""
    if dotenv_path is None:
        dotenv_path = get_project_root() / ".env"

    if not dotenv_path.exists():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")

                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        # Environment configuration may also be supplied externally.
        pass


def clean_markdown_fences(raw_text: str) -> str:
    """Remove surrounding Markdown code fences without altering SQL literals."""
    text = raw_text.strip()

    match = re.fullmatch(
        r"```(?:sql)?[ \t]*\r?\n?([\s\S]*?)\r?\n?```",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        text = match.group(1).strip()

    return text


class GroqSQLGenerator:
    """Generate and validate read-only SQL using the Groq API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
        validator: SQLSafetyValidator | None = None,
        default_limit: int = DEFAULT_ROW_LIMIT,
        max_limit: int = MAX_ROW_LIMIT,
    ):
        load_env_file()

        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = (
            model
            or os.environ.get("GROQ_MODEL")
            or DEFAULT_GROQ_MODEL
        )

        self.validator = validator or SQLSafetyValidator(
            default_limit=default_limit,
            max_limit=max_limit,
        )

        if client is not None:
            self.client = client
        else:
            if not self._api_key or not self._api_key.strip():
                raise GroqConfigurationError(
                    "GROQ_API_KEY environment variable is not set. "
                    "Please set GROQ_API_KEY or pass api_key to initialize "
                    "the generator."
                )

            self.client = groq.Groq(api_key=self._api_key)

    def verify_model_supported(self) -> bool:
        """Return whether the configured model is available on Groq."""
        try:
            models_response = self.client.models.list()
            available_ids = {model.id for model in models_response.data}
            return self.model in available_ids
        except GroqError as exc:
            raise GroqProviderError(
                f"Failed to query Groq model list: {exc}"
            ) from exc
        except Exception as exc:
            raise GroqProviderError(
                f"Unexpected error querying Groq models: {exc}"
            ) from exc

    def generate_sql(self, question: str) -> GenerationResult:
        """
        Generate SQL and validate it before returning.

        Raises:
            ValueError: If the question is empty.
            GroqProviderError: If the Groq request fails.
            SQLGenerationError: If the response is malformed or invalid.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        normalized_question = question.strip()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": NORTHWIND_SCHEMA_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": normalized_question,
                    },
                ],
                temperature=0.0,
            )
        except GroqError as exc:
            raise GroqProviderError(
                f"Groq API call failed: {exc}"
            ) from exc
        except Exception as exc:
            raise GroqProviderError(
                f"Unexpected error communicating with Groq: {exc}"
            ) from exc

        try:
            raw_text = completion.choices[0].message.content or ""
        except (AttributeError, IndexError, TypeError) as exc:
            raise SQLGenerationError(
                f"Malformed response structure from Groq: {exc}"
            ) from exc

        if not raw_text.strip():
            raise SQLGenerationError("Model returned an empty response.")

        clean_sql = clean_markdown_fences(raw_text)
        if not clean_sql:
            raise SQLGenerationError(
                "Extracted query from model response is empty."
            )

        # Model output is untrusted. Validate before any database execution.
        try:
            validation = self.validator.validate(clean_sql)
        except SQLValidationError as exc:
            raise SQLGenerationError(
                f"Generated SQL failed safety validation: {exc}\n"
                f"Generated SQL: {clean_sql}"
            ) from exc

        if not validation.is_valid:
            raise SQLGenerationError(
                "Generated SQL failed safety validation: "
                f"{validation.error}\n"
                f"Generated SQL: {clean_sql}"
            )

        if not validation.sanitized_sql:
            raise SQLGenerationError(
                "SQL validation returned no sanitized query."
            )

        return GenerationResult(
            question=normalized_question,
            raw_response=raw_text,
            sql=validation.sanitized_sql,
            model=self.model,
            tables_referenced=validation.tables,
        )
