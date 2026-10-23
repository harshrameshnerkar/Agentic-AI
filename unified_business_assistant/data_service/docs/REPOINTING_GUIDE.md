# Role B: Database Repointing & Migration Guide

## 1. Overview
The Role B Data Service is architected for zero-downtime database repointing. It abstracts the underlying storage engine behind the [DatabaseConnectionManager](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/unified_business_assistant/data_service/db/connection.py) and parameterizes the SQL generation dialect in [TextToSQLGenerator](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/unified_business_assistant/data_service/sql/generator.py).

This guide explains how to point the service to:
1. A different local or shared SQLite database.
2. A remote Cloud PostgreSQL instance (e.g. Neon, AWS RDS, GCP Cloud SQL).

---

## 2. Pointing to a Different SQLite Database

### Step 1: Update Environment Variable
In `data_service/.env` (or root `.env`):
```bash
# Point to your custom SQLite file path
SQL_DATABASE_PATH="C:/path/to/custom_business.db"
```

### Step 2: Ensure Read-Only Permissions
The connection manager automatically appends `?mode=ro` and executes `PRAGMA query_only = ON;`:
```python
# db/connection.py handles URI conversion automatically:
uri = f"file:{normalized_path}?mode=ro"
conn = sqlite3.connect(uri, uri=True)
conn.execute("PRAGMA query_only = ON;")
```

### Step 3: Reseed or Validate Schema
If creating a fresh instance:
```bash
python db/seed_database.py
```
To verify row counts:
```bash
curl http://127.0.0.1:8002/health
```

---

## 3. Pointing to PostgreSQL / Neon Database

### Step 1: Configure Database URL & Driver
Install the PostgreSQL driver:
```bash
pip install psycopg2-binary
```

Configure your `.env`:
```bash
DATABASE_ENGINE="postgresql"
DATABASE_URL="postgresql://readonly_user:password@ep-cool-db.neon.tech/neondb?sslmode=require"
SQL_DIALECT="postgres"
```

### Step 2: Provision a Read-Only Database Role (PostgreSQL)
In PostgreSQL, read-only enforcement is managed at the database permission level:
```sql
-- 1. Create dedicated read-only role
CREATE ROLE data_service_readonly WITH LOGIN PASSWORD 'strong_password';

-- 2. Grant connection and schema usage
GRANT CONNECT ON DATABASE neondb TO data_service_readonly;
GRANT USAGE ON SCHEMA public TO data_service_readonly;

-- 3. Grant SELECT only (strictly omit INSERT, UPDATE, DELETE, TRUNCATE)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_service_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO data_service_readonly;

-- 4. Session-level safety pragma
ALTER ROLE data_service_readonly SET default_transaction_read_only = TRUE;
```

### Step 3: Update Dialect in `safety/validator.py`
The AST parser supports PostgreSQL natively without code refactoring:
```python
# Pass dialect="postgres" to sqlglot
is_valid, validated_sql, _ = SQLSafetyValidator.validate(query, dialect="postgres")
```

---

## 4. Schema Refresh & Prompt Synchronization
When the database schema changes:
1. Open [sql/schema_context.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/unified_business_assistant/data_service/sql/schema_context.py).
2. Update `SCHEMA_METADATA` with the new tables or column definitions.
3. Update [docs/SCHEMA.md](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/unified_business_assistant/data_service/docs/SCHEMA.md).
4. Run the benchmark suite to verify accuracy against the new schema:
   ```bash
   python evaluation/run_evaluation.py
   ```
