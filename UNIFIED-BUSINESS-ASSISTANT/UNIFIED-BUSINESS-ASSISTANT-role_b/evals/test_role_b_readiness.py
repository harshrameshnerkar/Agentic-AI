
"""
Offline readiness evaluation for the Role B Data Service.

Checks:
1. The shared 40-question evaluation dataset has the expected structure.
2. The mock and real API health endpoints respond correctly.
3. Both API implementations accept valid requests and return JSON objects.
4. Mock and real API response contracts are compared and differences reported.
5. The real API's unanswerable and failure behavior is exercised using
   the existing offline test fixtures where possible.
6. Destructive SQL is rejected by the PostgreSQL validator before a
   database connection is opened.

This script does NOT:
- Call Groq or Neon.
- Execute SQL against a real database.
- Prove compatibility with Role C's actual orchestrator.
- Modify application code, evaluation data, or Git state.

Run from the repository root:
    .\\.venv\\Scripts\\python.exe evals/test_role_b_readiness.py

Exit code:
    0 = all required offline checks passed
    1 = one or more required offline checks failed
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

# Make imports work when the script is run directly from the repository root
# or by its relative path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXPECTED_CATEGORY_COUNTS = {
    "Knowledge": 15,
    "Data": 15,
    "Ambiguous": 5,
    "Unanswerable": 5,
}

MOCK_REQUIRED_FIELDS = {
    "success",
    "sql",
    "columns",
    "rows",
    "row_count",
    "error",
    "answerable",
}

REAL_REQUIRED_FIELDS = MOCK_REQUIRED_FIELDS

EXPECTED_DATA_ROUTE = "data_service"
EXPECTED_DATASET_SIZE = 40

results: list[tuple[str, bool, str]] = []


def report(name: str, passed: bool, detail: str) -> None:
    """Record and print a check result."""
    results.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}: {detail}")


def not_verified(name: str, detail: str) -> None:
    """Print a limitation that is not an offline test failure."""
    print(f"[NOT VERIFIED] {name}: {detail}")


def load_dataset() -> list[dict[str, Any]]:
    """Load the shared dataset and validate its basic structure."""
    path = ROOT / "merged_test_set.json"

    if not path.is_file():
        report("Dataset exists", False, f"Missing file: {path}")
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report("Dataset parses", False, f"{type(exc).__name__}: {exc}")
        return []

    if not isinstance(data, list):
        report("Dataset structure", False, "Expected a JSON list.")
        return []

    report("Dataset exists and parses", True, f"Loaded {len(data)} entries.")

    valid_objects = all(isinstance(item, dict) for item in data)
    if not valid_objects:
        report("Dataset entries", False, "Every entry must be a JSON object.")
        return []

    required_fields = {
        "id",
        "category",
        "question",
        "expected_route",
        "expected_answer",
    }

    missing = [
        (index, sorted(required_fields - item.keys()))
        for index, item in enumerate(data)
        if required_fields - item.keys()
    ]

    report(
        "Dataset required fields",
        not missing,
        "All entries contain required fields."
        if not missing
        else f"Missing fields by index: {missing[:5]}",
    )

    ids = [item.get("id") for item in data]
    ids_are_valid = all(isinstance(item_id, str) and item_id for item_id in ids)
    unique_ids = len(ids) == len(set(ids))

    report(
        "Dataset IDs",
        ids_are_valid and unique_ids,
        f"{len(ids)} IDs; valid={ids_are_valid}, unique={unique_ids}.",
    )

    report(
        "Dataset question count",
        len(data) == EXPECTED_DATASET_SIZE,
        f"Expected {EXPECTED_DATASET_SIZE}; found {len(data)}.",
    )

    category_counts = Counter(item.get("category") for item in data)
    report(
        "Dataset category counts",
        dict(category_counts) == EXPECTED_CATEGORY_COUNTS,
        f"Expected {EXPECTED_CATEGORY_COUNTS}; found {dict(category_counts)}.",
    )

    data_questions = [
        item for item in data if item.get("category") == "Data"
    ]
    wrong_data_routes = [
        item.get("id")
        for item in data_questions
        if item.get("expected_route") != EXPECTED_DATA_ROUTE
    ]

    report(
        "Data question routing labels",
        len(data_questions) == 15 and not wrong_data_routes,
        f"Data questions={len(data_questions)}; "
        f"incorrect route IDs={wrong_data_routes}.",
    )

    return data



def validate_mock_response(body: Any) -> list[str]:
    """Validate the response shape used by the current Role B APIs."""
    errors: list[str] = []

    if not isinstance(body, dict):
        return ["Response must be a JSON object."]

    missing = MOCK_REQUIRED_FIELDS - body.keys()
    if missing:
        return [f"Missing fields: {sorted(missing)}"]

    if not isinstance(body["success"], bool):
        errors.append("'success' must be a boolean.")

    if not isinstance(body["answerable"], bool):
        errors.append("'answerable' must be a boolean.")

    if body["sql"] is not None and not isinstance(body["sql"], str):
        errors.append("'sql' must be a string or null.")

    columns = body["columns"]
    if not isinstance(columns, list) or not all(
        isinstance(column, str) for column in columns
    ):
        errors.append("'columns' must be a list of strings.")

    rows = body["rows"]
    if not isinstance(rows, list):
        errors.append("'rows' must be a list.")
    elif not all(isinstance(row, dict) for row in rows):
        errors.append("Every row must be a dictionary.")
    elif isinstance(columns, list) and all(
        isinstance(column, str) for column in columns
    ):
        expected_columns = set(columns)

        if len(expected_columns) != len(columns):
            errors.append("'columns' must not contain duplicate names.")

        for index, row in enumerate(rows):
            if len(row) != len(columns):
                errors.append(
                    f"Row {index} has {len(row)} values; "
                    f"expected {len(columns)}."
                )

            if list(row.keys()) != columns:
                errors.append(
                    f"Row {index} keys do not match the columns."
                )

    row_count = body["row_count"]
    if (
        not isinstance(row_count, int)
        or isinstance(row_count, bool)
        or row_count < 0
    ):
        errors.append("'row_count' must be a non-negative integer.")
    elif isinstance(rows, list) and row_count != len(rows):
        errors.append("'row_count' does not match len(rows).")

    error = body["error"]
    if error is not None and not isinstance(error, str):
        errors.append("'error' must be a string or null.")

    if body["success"] is True and error is not None:
        errors.append("Successful response must have error=null.")

    if body["success"] is False and (
        not isinstance(error, str) or not error.strip()
    ):
        errors.append("Failed response must include an error.")

    return errors




def validate_real_response(body: Any) -> list[str]:
    """Validate the real API against the shared Role B contract."""
    return validate_mock_response(body)



def check_api_endpoints() -> None:
    """Exercise both API apps in-process, without opening network ports."""
    try:
        from main import app as mock_app
    except Exception as exc:
        report(
            "Mock API import",
            False,
            f"{type(exc).__name__}: {exc}",
        )
        mock_app = None

    try:
        from real_api import app as real_app
    except Exception as exc:
        report(
            "Real API import",
            False,
            f"{type(exc).__name__}: {exc}",
        )
        real_app = None

    mock_success: dict[str, Any] | None = None
    real_success: dict[str, Any] | None = None

    if mock_app is not None:
        with TestClient(mock_app) as client:
            try:
                response = client.get("/health")
                body = response.json()
                report(
                    "Mock health",
                    response.status_code == 200
                    and isinstance(body, dict)
                    and body.get("status") == "ok",
                    f"HTTP {response.status_code}; body={body!r}",
                )
            except Exception as exc:
                report(
                    "Mock health",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

            try:
                response = client.post(
                    "/query",
                    json={"question": "Show the top-selling products"},
                )
                mock_success = response.json()
                errors = validate_mock_response(mock_success)
                report(
                    "Mock success response contract",
                    response.status_code == 200 and not errors,
                    f"HTTP {response.status_code}; errors={errors}; "
                    f"keys={sorted(mock_success) if isinstance(mock_success, dict) else type(mock_success).__name__}.",
                )
            except Exception as exc:
                report(
                    "Mock success response contract",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

            try:
                response = client.post(
                    "/query",
                    json={"question": "   "},
                )
                body = response.json()
                errors = validate_mock_response(body)
                report(
                    "Mock whitespace handling",
                    response.status_code == 200
                    and not errors
                    and body.get("success") is False,
                    f"HTTP {response.status_code}; errors={errors}.",
                )
            except Exception as exc:
                report(
                    "Mock whitespace handling",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

    if real_app is not None:
        with TestClient(real_app) as client:
            try:
                response = client.get("/health")
                body = response.json()
                report(
                    "Real API health",
                    response.status_code == 200
                    and isinstance(body, dict)
                    and body.get("status") == "ok",
                    f"HTTP {response.status_code}; body={body!r}",
                )
            except Exception as exc:
                report(
                    "Real API health",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

            # The real API normally constructs its generator lazily.
            # This readiness check replaces that factory with an offline fake.
            
            try:
                from real_api import create_app
                from tests.test_real_api import FakeGenerator

                fake_client = TestClient(
                    create_app(
                        generator_factory=lambda: FakeGenerator()
                    )
                )

                with fake_client:
                    response = fake_client.post(
                        "/query",
                        json={"question": "Show a sample customer"},
                    )

                real_success = response.json()
                errors = validate_real_response(real_success)

                report(
                    "Real API success response contract (fake generator)",
                    response.status_code == 200 and not errors,
                    f"HTTP {response.status_code}; errors={errors}; "
                    f"keys={sorted(real_success) if isinstance(real_success, dict) else type(real_success).__name__}.",
                )
            except Exception as exc:
                report(
                    "Real API success response contract (fake generator)",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

            try:
                response = client.post(
                    "/query",
                    json={"question": "   "},
                )
                body = response.json()
                errors = validate_real_response(body)
                report(
                    "Real API whitespace handling",
                    response.status_code == 200
                    and not errors
                    and body.get("success") is False,
                    f"HTTP {response.status_code}; errors={errors}.",
                )
            except Exception as exc:
                report(
                    "Real API whitespace handling",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

    # Report schema differences without assuming which API should change.
    if isinstance(mock_success, dict) and isinstance(real_success, dict):
        mock_fields = set(mock_success)
        real_fields = set(real_success)

        report(
            "Mock/real field-set parity",
            mock_fields == real_fields,
            f"Only mock: {sorted(mock_fields - real_fields)}; "
            f"only real: {sorted(real_fields - mock_fields)}.",
        )

        mock_rows = mock_success.get("rows")
        real_rows = real_success.get("rows")
        row_format_same = (
            not mock_rows
            or not real_rows
            or type(mock_rows[0]) is type(real_rows[0])
        )
        report(
            "Mock/real row-format parity",
            row_format_same,
            f"Mock row type={type(mock_rows[0]).__name__ if mock_rows else 'no rows'}; "
            f"real row type={type(real_rows[0]).__name__ if real_rows else 'no rows'}.",
        )
    else:
        not_verified(
            "Mock/real schema comparison",
            "At least one success response could not be collected.",
        )


def check_sql_safety() -> None:
    """Test SQL validation only; never execute SQL against PostgreSQL."""
    try:
        from src.safety.postgres_validator import (
            PostgresSQLValidationError,
            PostgresSafetyValidator,
        )
    except Exception as exc:
        report(
            "SQL validator import",
            False,
            f"{type(exc).__name__}: {exc}",
        )
        return

    validator = PostgresSafetyValidator(connection_factory=MagicMock())

    safe_queries = [
        "SELECT customername FROM customers",
        "SELECT productname FROM products LIMIT 5",
    ]

    safe_errors = []
    for query in safe_queries:
        try:
            validator.validate(query)
        except Exception as exc:
            safe_errors.append(f"{query!r}: {type(exc).__name__}: {exc}")

    report(
        "Safe SQL validation",
        not safe_errors,
        "Approved SELECT statements accepted."
        if not safe_errors
        else "; ".join(safe_errors),
    )

    destructive_queries = [
        "DELETE FROM customers",
        "UPDATE customers SET city = 'x'",
        "INSERT INTO customers(customername) VALUES ('x')",
        "DROP TABLE customers",
        "SELECT * INTO new_table FROM customers",
        "SELECT * FROM customers; DROP TABLE customers",
    ]

    rejected: list[str] = []
    unexpectedly_accepted: list[str] = []

    for query in destructive_queries:
        try:
            validator.validate(query)
        except PostgresSQLValidationError:
            rejected.append(query)
        except Exception as exc:
            unexpectedly_accepted.append(
                f"{query!r}: unexpected {type(exc).__name__}: {exc}"
            )
        else:
            unexpectedly_accepted.append(query)

    report(
        "Destructive SQL rejected",
        not unexpectedly_accepted,
        f"Rejected {len(rejected)}/{len(destructive_queries)} cases."
        if not unexpectedly_accepted
        else f"Unexpected outcomes: {unexpectedly_accepted}",
    )

    connection_factory = MagicMock()
    no_connection_validator = PostgresSafetyValidator(
        connection_factory=connection_factory
    )

    try:
        no_connection_validator.execute("DELETE FROM customers")
    except PostgresSQLValidationError:
        pass
    except Exception as exc:
        report(
            "Unsafe SQL blocked before connection",
            False,
            f"Unexpected {type(exc).__name__}: {exc}",
        )
        return
    else:
        report(
            "Unsafe SQL blocked before connection",
            False,
            "Destructive SQL was not rejected.",
        )
        return

    report(
        "Unsafe SQL blocked before connection",
        not connection_factory.called,
        "Connection factory was not called for rejected SQL.",
    )


def main() -> int:
    print("=" * 72)
    print("ROLE B DATA SERVICE — OFFLINE READINESS EVALUATION")
    print("=" * 72)
    print(f"Repository: {ROOT}")
    print("Mode: offline; no live Groq/Neon calls intended\n")

    load_dataset()
    print("\n--- API checks ---")
    check_api_endpoints()

    print("\n--- SQL safety checks ---")
    check_sql_safety()

    print("\n--- Integration limitations ---")
    not_verified(
        "Role C compatibility",
        "Role C's actual request/response contract and implementation "
        "have not been tested.",
    )
    not_verified(
        "Live Groq and PostgreSQL",
        "No live generation or database query was performed.",
    )
    not_verified(
        "End-to-end routing score",
        "The dataset's routing labels were checked; the orchestrator "
        "did not process all 40 questions.",
    )
    not_verified(
        "Service-down recovery",
        "No running integrated system was shut down during this test.",
    )

    failures = [result for result in results if not result[1]]
    passes = len(results) - len(failures)

    print("\n" + "=" * 72)
    print(f"SUMMARY: {passes}/{len(results)} required checks passed.")
    print(f"Failed checks: {len(failures)}")
    for name, _, detail in failures:
        print(f"  - {name}: {detail}")
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
