# Day 4 — Session 2: Writing Good Tools

## 1. Executive Summary & Learning Goals

Building production-ready tools for AI agents requires more than wrapping functions. LLMs rely entirely on your tool's schema, name, and error reporting to make intelligent decisions.

### The 5 Core Principles of Good Tool Design:

1. **Naming**:
   - Use clear, unambiguous, lower_case_with_underscores, imperative verb-noun names.
   - Examples: `web_search`, `read_file`, `query_database`, `send_email`.
   - Avoid vague names like `get_data`, `run_query`, `process_info`.

2. **Descriptions Written for the Model**:
   - The tool description is a **mini-prompt** seen by the LLM on every turn.
   - Explicitly tell the model **when to use it** and **when NOT to use it**.
   - Embed table schemas directly in the description of database tools so the model doesn't guess column names!

3. **Typed & Validated Arguments**:
   - Always declare JSON Schema types (`string`, `integer`, `array`, `boolean`).
   - Validate arguments inside Python before execution (e.g. RFC 5322 email regex, sandbox path traversal prevention).

4. **Keeping Tool Count Small**:
   - Don't expose 25 micro-tools (e.g. `read_env`, `read_json`, `read_csv`, `read_txt`).
   - Consolidate into 4 clean, robust capabilities to avoid cognitive overload and token waste.

5. **Returning Errors as Observations**:
   - **CRITICAL AGENTIC PATTERN**: Never let the host runtime raise an unhandled exception or crash!
   - Catch errors and return them as structured JSON observations:
     ```json
     {
       "status": "error",
       "error_type": "OperationalError",
       "message": "no such column: full_name",
       "schema_reference": {"employees": ["id", "name", "department", "role", "salary", "email"]},
       "hint": "Check table and column names against the schema_reference and self-correct your SQL query."
     }
     ```
   - This empowers the agent to inspect the error, adjust its reasoning, and self-correct on the next turn!

---

## 2. The 4 Production Tools Built

| Tool Name | Module | Responsibility | Key Guardrails & Features |
| :--- | :--- | :--- | :--- |
| **`web_search`** | [web_search_tool.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_04/session_2/web_search_tool.py) | Searches recent external documentation, tech release notes, weather, news. | Query length validation, bounded results (1-10), observation returns on empty results. |
| **`read_file`** | [file_reader_tool.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_04/session_2/file_reader_tool.py) | Safely reads local workspace text/code/config files. | Directory traversal sandboxing (blocks `../../`), pagination (`start_line`, `max_lines`), sibling file hints on missing files. |
| **`query_database`** | [database_tool.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_04/session_2/database_tool.py) | Queries enterprise SQLite database (`employees`, `orders`, `inventory`). | Read-only enforcement (blocks `DROP`, `DELETE`, `UPDATE`), schema hints on syntax/column errors. |
| **`send_email`** | [email_tool.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_04/session_2/email_tool.py) | Dispatches notifications via mock gateway with audit trail. | RFC 5322 regex validation, unique Message ID generation, persistent audit logging to `sent_emails.jsonl`. |

---

## 3. Architecture & File Structure

```
day_04/session_2/
├── web_search_tool.py   # Tool 1: Web Search with relevance scoring
├── file_reader_tool.py  # Tool 2: Sandboxed File Reader with line pagination
├── database_tool.py     # Tool 3: Read-only SQLite query tool with schema hints
├── email_tool.py        # Tool 4: Mock email sender with regex validation and audit trail
├── database_setup.py    # Database seed script creating enterprise.db
├── schemas.py           # Production JSON Schema definitions written for the model
├── tool_runtime.py      # Safe dispatcher implementing the Error-as-Observation pattern
├── agent.py             # Multi-step autonomous agent with error recovery and retry backoff
├── evaluator.py         # Automated test suite verifying all 4 tools and multi-step chains
├── main.py              # Master interactive walkthrough
├── sample_policy.txt    # Sample workspace text file for reader testing
├── enterprise.db        # SQLite database populated with realistic records
├── requirements.txt     # Python dependencies
└── .env                 # API credentials and model configuration
```

---

## 4. Execution Commands

```powershell
cd C:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_04\session_2

# 1. Test individual tools locally
python web_search_tool.py
python file_reader_tool.py
python database_tool.py
python email_tool.py

# 2. Inspect the model-facing JSON Schemas
python schemas.py

# 3. Run the automated evaluation suite
python evaluator.py

# 4. Run the master walkthrough
python main.py
```
