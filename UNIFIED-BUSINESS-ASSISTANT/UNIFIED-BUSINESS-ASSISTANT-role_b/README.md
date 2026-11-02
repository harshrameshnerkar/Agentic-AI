# Unified Business Assistant — Role B

Role B provides the database and data-query service for the Unified Business Assistant project.

## Current status

Role B provides two API entry points:

- `main.py`: deterministic mock API for Role C integration. It returns demonstration data and does not generate or execute SQL.
- `real_api.py`: PostgreSQL-backed API that generates SQL using Groq, validates queries, and executes approved read-only queries against the configured PostgreSQL database.

Both APIs expose `/health` and `/query`. The mock is retained for integration testing; the real API is a separate entry point.

## Requirements

- Python and the project virtual environment
- Dependencies listed in `requirements.txt`
- For the real API: a Groq API key and PostgreSQL connection string

## Setup

From the project root, install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local `.env` using `.env.example` as a template. Set your real credentials locally. Never commit `.env` or share its secrets.

Configuration:

- `GROQ_API_KEY`: required for real SQL generation
- `GROQ_MODEL`: model identifier; the generator has a default
- `NEONDB_URL`: PostgreSQL connection string; `DATABASE_URL` is also supported as a fallback by the validator

## Running the APIs

### Mock API

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Base URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### Real PostgreSQL API

```powershell
.\.venv\Scripts\python.exe -m uvicorn real_api:app --reload --host 127.0.0.1 --port 8001
```

Base URL: `http://127.0.0.1:8001`

The real API requires valid Groq and PostgreSQL configuration for query execution. The mock API does not require a live database.

These commands are intended for local development. Configure authentication and deployment networking before exposing the service outside a trusted environment.

## Endpoints

### GET `/health`

Checks whether the API process responds. The exact response may differ between the mock and real implementations.

### POST `/query`

Request:

```json
{
  "question": "Show the top 5 products by sales"
}
```

Illustrative response:

```json
{
  "success": true,
  "sql": "SELECT ...",
  "columns": ["product_name", "total_sales"],
  "rows": [
    {
      "product_name": "Product A",
      "total_sales": 1500.0
    },
    {
      "product_name": "Product B",
      "total_sales": 1200.0
    }
  ],
  "row_count": 2,
  "answerable": true,
  "error": null
}
```

The example is illustrative and does not represent a verified live database result. Actual columns and results depend on the database and question. The mock returns sample data rather than executing SQL.

### Response fields

| Field | Type | Meaning |
|---|---|---|
| `success` | Boolean | Whether the request succeeded; an implementation-specific field |
| `sql` | String or null | Generated SQL or a mock marker; the failure representation requires contract alignment |
| `columns` | Array of strings | Result column names in their defined order |
| `rows` | Array of objects | Query result rows, with column names as object keys |
| `row_count` | Integer | Number of returned rows |
| `answerable` | Boolean | Indicates whether the question can be answered using the available data |
| `error` | String, when applicable | Error message when a query fails or cannot be generated |

Each object in `rows` maps column names to their corresponding values. The keys should match the names and order in `columns`. An empty result is represented by `"rows": []` and `"row_count": 0`.

The shared response contract requires `sql`, `rows`, `columns`, `row_count`, and `answerable`. It specifies that `error` is present only when a query fails or cannot be generated. The current implementations also include `success` and may return `"error": null` on success. Aligning these implementation-specific behaviors with the shared contract must be handled separately after confirming Role C's expectations.

For failures, the current implementation returns `success: false`, empty result data, and an error message. The exact SQL representation and error-field behavior should be verified against the agreed contract before integration is accepted.

A missing or empty `question` is rejected by request validation with HTTP 422. A whitespace-only question returns a failure response with an error message.

Role C should inspect `answerable` before presenting the result as an answer. When `answerable` is `false`, the client should follow the agreed fallback behavior rather than presenting the query result as a successful answer.

## Query safety

The PostgreSQL validator is designed to:

- Validate SQL before execution.
- Reject destructive statements and disallowed SQL constructs.
- Restrict access to approved tables and reject dangerous PostgreSQL functions.
- Apply result limits and a statement timeout.
- Execute queries in a read-only transaction.
- Roll back and close the database connection after execution.

These controls must be verified with tests. A read-only transaction is defense in depth; a dedicated database role with read-only permissions is also recommended. Do not interpret these controls as a guarantee against every possible attack.

## Run tests

Run API tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_api.py" -v
```

Run the complete test suite using `unittest`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the project's pytest suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the offline readiness evaluation:

```powershell
.\.venv\Scripts\python.exe .\evals\test_role_b_readiness.py
```

The offline readiness evaluation checks the dataset, response contracts, and SQL safety without requiring live Groq or Neon calls. Passing offline tests does not prove live database execution or Role C compatibility.

Record live database and Role C integration results separately from offline test results.

## Database documentation

See [`docs/northwind_schema.md`](docs/northwind_schema.md) for the Northwind reference schema and relationships.

See [`docs/postgres_data_service.md`](docs/postgres_data_service.md) for PostgreSQL service configuration, the response contract, and safety details.

The Northwind SQLite schema and its row counts must not be treated as a live inventory of the configured PostgreSQL database.

## Integration note

Keep `main.py` available as the deterministic mock endpoint. Use `real_api.py` as the separate PostgreSQL-backed service when validating real text-to-SQL integration with Role C.

Before accepting the integration, verify:

- The shared request and response contract.
- Dictionary-shaped result rows and column ordering.
- The required `answerable` field and Role C's handling of it.
- Error handling, including whether `error` is omitted on success.
- Failure behavior and the representation of `sql` when generation or execution fails.
- Live Groq and PostgreSQL execution using the team's agreed test questions.

Confirm the real service with the team's test questions and logs. Mock responses and offline tests alone do not establish successful live integration.