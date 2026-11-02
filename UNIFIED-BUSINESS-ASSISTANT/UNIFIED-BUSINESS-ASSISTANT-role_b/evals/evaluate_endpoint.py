
"""Live HTTP evaluation for the Role B Data Service mock API.

Checks connectivity, health, request validation, and the /query response
contract. This evaluates the current mock; it does not prove database
execution or Groq integration.
"""

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REQUIRED_FIELDS = {
    "success",
    "sql",
    "columns",
    "rows",
    "row_count",
    "error",
    "answerable",
}

class EndpointUnavailable(Exception):
    """Raised when the HTTP endpoint cannot be reached."""


def request_json(base_url, path, method="GET", payload=None, timeout=5):
    """Send an HTTP request and return its status and decoded JSON."""
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            raw_body = response.read()
    except HTTPError as exc:
        status = exc.code
        raw_body = exc.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise EndpointUnavailable(str(exc)) from exc

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        body = None

    return status, body


def validate_response_contract(body):
    """Return contract errors without assuming database results."""
    errors = []

    if not isinstance(body, dict):
        return ["Response body must be a JSON object."]

    missing = REQUIRED_FIELDS - body.keys()
    if missing:
        errors.append(f"Missing fields: {sorted(missing)}")
        return errors

    if not isinstance(body["success"], bool):
        errors.append("'success' must be a boolean.")

    if body["sql"] is not None and not isinstance(body["sql"], str):
        errors.append("'sql' must be a string or null.")

    if not isinstance(body["columns"], list) or not all(
        isinstance(column, str) for column in body["columns"]
    ):
        errors.append("'columns' must be a list of strings.")

    if not isinstance(body["rows"], list):
        errors.append("'rows' must be a list.")
    elif not all(isinstance(row, dict) for row in body["rows"]):
        errors.append("Every row must be a dictionary.")
    elif isinstance(body["columns"], list) and all(
        isinstance(column, str) for column in body["columns"]
    ):
        for index, row in enumerate(body["rows"]):
            if list(row.keys()) != body["columns"]:
                errors.append(
                    f"Row {index} keys must match columns in order."
                )

    if (
        not isinstance(body["row_count"], int)
        or isinstance(body["row_count"], bool)
        or body["row_count"] < 0
    ):
        errors.append("'row_count' must be a non-negative integer.")
    elif isinstance(body["rows"], list):
        if body["row_count"] != len(body["rows"]):
            errors.append("'row_count' does not match the number of rows.")

    if not isinstance(body["answerable"], bool):
        errors.append("'answerable' must be a boolean.")

    if body["error"] is not None and not isinstance(body["error"], str):
        errors.append("'error' must be a string or null.")

    if body["success"] and body["error"] is not None:
        errors.append("Successful responses must have error=null.")

    if not body["success"] and not body["error"]:
        errors.append("Failed responses must include an error message.")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the running Role B HTTP API."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5,
        help="Request timeout in seconds (default: 5)",
    )
    args = parser.parse_args()

    results = []

    def report(name, passed, detail):
        status = "PASS" if passed else "FAIL"
        results.append(passed)
        print(f"[{status}] {name}: {detail}")

    def skip(name, reason):
        print(f"[SKIP] {name}: {reason}")

    print(f"\nRole B endpoint evaluation: {args.base_url}\n")

    # 1. Health and connectivity
    try:
        status, body = request_json(
            args.base_url, "/health", timeout=args.timeout
        )
    except EndpointUnavailable as exc:
        report("API connectivity", False, str(exc))
        for name in (
            "Health response",
            "Valid query and response contract",
            "Whitespace question",
            "Empty question validation",
            "Missing question validation",
        ):
            skip(name, "API is unreachable.")
        print("\nStart the API with: python -m uvicorn main:app --reload")
        print(f"Result: {sum(results)}/{len(results)} checks passed.")
        return 1

    report("API connectivity", True, "HTTP endpoint is reachable.")
    report(
        "Health response",
        status == 200
        and isinstance(body, dict)
        and body.get("status") == "ok"
        and body.get("service") == "role-b-data-service",
        f"HTTP {status}; body={body!r}",
    )

    # 2. Valid request and response contract
    try:
        status, body = request_json(
            args.base_url,
            "/query",
            method="POST",
            payload={"question": "Show top products"},
            timeout=args.timeout,
        )
        errors = validate_response_contract(body)
        passed = (
            status == 200
            and not errors
            and body["success"] is True
            and isinstance(body["sql"], str)
            and isinstance(body["columns"], list)
            and len(body["columns"]) > 0
            and isinstance(body["rows"], list)
            and body["error"] is None
        )
        if errors:
            detail = "; ".join(errors)
        elif not passed:
            detail = f"Unexpected response: HTTP {status}; {body!r}"
        else:
            detail = (
                f"HTTP {status}; {body['row_count']} rows; "
                f"columns={body['columns']!r}"
            )
        report("Valid query and response contract", passed, detail)

        if passed:
            is_mock = (
                "MOCK ONLY" in body["sql"]
                and body["columns"] == ["ProductName", "TotalSales"]
            )
            if is_mock:
                print(
                    "[INFO] The endpoint returned mock data; "
                    "Groq and database execution are not verified."
                )
    except EndpointUnavailable as exc:
        report("Valid query and response contract", False, str(exc))

    # 3. Whitespace-only question: structured failure with HTTP 200
    try:
        status, body = request_json(
            args.base_url,
            "/query",
            method="POST",
            payload={"question": "   "},
            timeout=args.timeout,
        )
        passed = (
            status == 200
            and isinstance(body, dict)
            and not validate_response_contract(body)
            and body["success"] is False
            and body["sql"] is None
            and body["columns"] == []
            and body["rows"] == []
            and body["row_count"] == 0
            and bool(body["error"])
        )
        report(
            "Whitespace question",
            passed,
            f"HTTP {status}; body={body!r}",
        )
    except EndpointUnavailable as exc:
        report("Whitespace question", False, str(exc))

    # 4. Empty question: Pydantic request validation should return HTTP 422
    for name, payload in (
        ("Empty question validation", {"question": ""}),
        ("Missing question validation", {}),
    ):
        try:
            status, _ = request_json(
                args.base_url,
                "/query",
                method="POST",
                payload=payload,
                timeout=args.timeout,
            )
            report(name, status == 422, f"HTTP {status}; expected HTTP 422.")
        except EndpointUnavailable as exc:
            report(name, False, str(exc))

    passed_count = sum(results)
    total = len(results)
    print(f"\nResult: {passed_count}/{total} checks passed.")
    print("Scope: live HTTP API and mock contract only.")
    print("No database writes or SQL execution were performed.")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
