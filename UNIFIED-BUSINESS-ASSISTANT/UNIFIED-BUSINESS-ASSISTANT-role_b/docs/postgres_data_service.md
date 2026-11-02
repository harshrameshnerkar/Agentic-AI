# Role B — PostgreSQL Data Service

## Overview

Role B provides a FastAPI service that converts natural-language questions into SQL using Groq and executes validated, read-only queries against PostgreSQL.

The original mock API remains available separately in `main.py`. The PostgreSQL-backed API is implemented in `real_api.py`.

## Requirements

- Python and the project's virtual environment
- Groq API key
- Neon PostgreSQL database and connection string
- Dependencies from `requirements.txt`

## Configuration

Create a local `.env` file using `.env.example` as a template.

Required settings:

- `GROQ_API_KEY`: Groq API key
- `NEONDB_URL`: PostgreSQL connection string
- `GROQ_MODEL`: Optional model override. The generator defaults to `openai/gpt-oss-120b`.

Never commit `.env` or expose credentials in logs, screenshots, or API responses.

## Start the service

Activate the virtual environment and run:

```powershell
python -m uvicorn real_api:app --host 127.0.0.1 --port 8001
```

The local address is intended for development. Configure deployment networking and authentication separately before exposing the service beyond a trusted environment.

## Endpoints

### `GET /health`

Health endpoint for checking whether the API process responds.

### `POST /query`

Accepts a natural-language question and returns the generated SQL and query result.

Request:

```json
{
  "question": "How many customers are in the database?"
}
```

Successful response example (illustrative):

```json
{
  "success": true,
  "sql": "SELECT COUNT(*) AS customer_count FROM public.customers LIMIT 100",
  "columns": ["customer_count"],
  "rows": [
    {
      "customer_count": 91
    }
  ],
  "row_count": 1,
  "answerable": true,
  "error": null
}
```

This example is illustrative and is not evidence of a current live database result. Actual rows and counts depend on the database contents.

The shared response contract requires the following fields:

| Field | Type | Meaning |
|---|---|---|
| `sql` | String or null | Generated SQL, or null when unavailable |
| `rows` | Array of objects | Query result rows, with column names as object keys |
| `columns` | Array of strings | Result column names in order |
| `row_count` | Integer | Number of returned rows |
| `answerable` | Boolean | Indicates whether the question can be answered by the query result |

Each object in `rows` maps column names to their corresponding values. For example:

```json
{
  "columns": ["ProductName", "TotalSales"],
  "rows": [
    {
      "ProductName": "Sample Product A",
      "TotalSales": 1500.0
    },
    {
      "ProductName": "Sample Product B",
      "TotalSales": 1200.0
    }
  ],
  "row_count": 2,
  "answerable": true
}
```

The `answerable` field must be interpreted by the client. When it is `false`, the client should not present the result as a successful answer to the user's question.

Failure response example (illustrative):

```json
{
  "success": false,
  "sql": null,
  "columns": [],
  "rows": [],
  "row_count": 0,
  "answerable": false,
  "error": "Unable to generate a valid query for this question."
}
```

The failure example illustrates the expected response shape; the exact error message depends on the failure condition.

The current implementation also includes `success` and `error`. These are implementation-specific response fields and should not be assumed to be part of the required shared contract without confirming compatibility with Role C.

In the current implementation, `success` indicates whether the request succeeded, while `error` contains an error message on failure and is `null` on success. The shared contract specifies that `error` is present only when the query fails or cannot be generated. Aligning the runtime's successful-response behavior with that requirement should be handled separately after confirming Role C's expectations.

Role C can use `sql` to display the generated query and use `columns` with dictionary-shaped `rows` to render a result table. It should also inspect `answerable` before presenting the result as an answer.

## Query safety

The PostgreSQL validator is designed to:

- Parse and validate SQL before execution.
- Reject destructive statements and disallowed SQL constructs.
- Restrict access to approved tables and reject dangerous PostgreSQL functions.
- Apply a default result limit and enforce a configured maximum.
- Execute queries in a read-only transaction.
- Set a statement timeout.
- Roll back and close the connection after execution.

These controls should be tested whenever the validator, database permissions, or schema changes. A read-only application transaction is defense in depth; a dedicated database role with read-only permissions is also recommended.

## Verification

**Historical development results — not a current verification run**

The following results were recorded during an earlier development session:

- Full automated suite: 115 passed, 8 subtests passed.
- Live Groq-to-Neon request: returned a successful response with one result row and a customer count of 91.
- `git diff --check`: reported no whitespace errors at that time; Git reported a line-ending conversion warning.

These historical results do not establish the current state of the code, database, or deployment.

During a later development verification run, the following results were reported:

- API-focused tests: 18 passed, 1 warning, 4 subtests passed.
- Full automated suite: 147 passed, 1 warning, 92 subtests passed.
- The warning concerned the deprecation of using `httpx` with `starlette.testclient`.

These tests passed in the reported local environment. They do not establish that a live Groq-to-Neon request was performed during that run, nor do they guarantee that every possible query or deployment configuration is safe.

## Database schema reference

`docs/northwind_schema.md` documents the SQLite Northwind reference schema. Do not treat its database engine or row counts as a live inventory of the Neon database.
