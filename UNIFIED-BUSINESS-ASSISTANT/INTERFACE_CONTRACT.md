# INTERFACE CONTRACT - AGREE AND COMMIT THIS ON DAY 1

> **Status**: AGREED & COMMITTED  
> **Version**: 1.0.0  
> **Service Architecture**: Unified Business Assistant (Role A + Role B + Role C) 

---

## 1. Overview & Service Roles

The **Unified Business Assistant** is partitioned into three distinct roles to enable parallel development on Day 1:

| Role | Service Name | Responsibility | Interfaces |
| :--- | :--- | :--- | :--- |
| **Role A** | **Knowledge Service** | Corporate Policy RAG over 50 enterprise PDFs | **Provides** Interface 1 (`POST /search`) |
| **Role B** | **Data Service** | Text-to-SQL over Northwind transactional database | **Provides** Interface 2 (`POST /query`) |
| **Role C** | **Orchestration & Evaluation** | Query Routing, Multi-Domain Synthesis, Fallbacks & Evaluation | **Provides** Interface 3 (Routing Decision)<br>**Consumes** Interface 1 & 2 |

---

## 2. INTERFACE 1 - Knowledge Service `/search`
- **Provided by**: Role A
- **Consumed by**: Role C
- **Purpose**: Role C sends a natural-language question and gets back ranked document passages with enough metadata to cite them.

### Request Specification (`POST /search`)
| Field | Type | Required | Default | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `query` | `string` | **Yes** | - | The user question, unmodified | `"What is the refund window?"` |
| `top_k` | `int` | No | `5` | Maximum number of ranked passages | `5` |
| `filters` | `object` | No | `{}` | Optional metadata filter keys (e.g. company, department) | `{"department": "finance"}` |

### Response Specification
| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `results` | `list[object]` | **Yes** | Ordered best-first; empty if no relevant passages | `[...]` |
| `results[].text` | `string` | **Yes** | The extracted passage text | `"Refunds are processed within 14 business days..."` |
| `results[].source` | `string` | **Yes** | Source document file name for citation | `"policy_handbook.pdf"` |
| `results[].page` | `int` | **Yes** | 1-indexed document page number | `14` |
| `results[].score` | `float` | **Yes** | Relevance score (normalized 0.0 to 1.0) | `0.82` |
| `no_match` | `bool` | **Yes** | `true` when nothing relevant was found (Role C must handle this to prevent hallucination) | `false` |

---

## 3. INTERFACE 2 - Data Service `/query`
- **Provided by**: Role B
- **Consumed by**: Role C
- **Purpose**: Role C sends a natural-language question about structured data and gets back rows plus the SQL that produced them.

### Request Specification (`POST /query`)
| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `question` | `string` | **Yes** | The user question, unmodified | `"Total sales by region last quarter"` |

### Response Specification
| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `sql` | `string` | **Yes** | SQL statement generated and executed (so C can show it to user) | `"SELECT region, SUM(amount) AS total FROM sales GROUP BY region;"` |
| `rows` | `list[dict]` | **Yes** | Query result rows (may be empty; bounded by agreed limit) | `[{"region": "West", "total": 40321}]` |
| `columns` | `list[string]` | **Yes** | Column names in order | `["region", "total"]` |
| `row_count` | `int` | **Yes** | Total number of returned rows | `4` |
| `error` | `string` | No | Present only when query failed or could not be generated | `"Unknown column 'profit'"` |
| `answerable` | `bool` | **Yes** | `false` when schema cannot answer it (Role C must handle fallback) | `true` |

---

## 4. INTERFACE 3 - Routing Decision
- **Provided by**: Role C
- **Consumed by**: Roles A and B
- **Purpose**: How Role C decides which service handles a question. Roles A and B need to understand what traffic they will receive.

### Decision Fields
| Field | Type | Required | Allowed Values / Rule | Example |
| :--- | :--- | :--- | :--- | :--- |
| `route` | `enum` | **Yes** | `knowledge` \| `data` \| `both` \| `none` | `"data"` |
| `routing_rule` | `string` | **Yes** | Explicit rule triggered by classifier | `"Aggregates, counts, tables and database entities go to data"` |
| `fallback` | `string` | **Yes** | Action to take when primary service fails | `"If data returns answerable=false, try knowledge; if both fail, declare unanswerable"` |

### Routing Rulebook:
1. **`data`**:
   - Queries asking for counts, aggregates (sum, average, max, min), tabular records, product catalogs, order dates, customer names, shipping details, or unit prices.
2. **`knowledge`**:
   - Queries asking about company policies, ethical rules, whistleblower mechanisms, POSH guidelines, ESG commitments, parental leave, DEI, code of conduct, or document retention.
3. **`both` (Hybrid/Cross-Domain)**:
   - Queries combining database entities with policy constraints (e.g., *"Check our employee handbook to see if any customers from Germany are violating our gift policies"*).
   - Execution Order: Role C queries Data Service for entities -> feeds entities to Knowledge Service -> synthesizes unified response.
4. **`none` (Unanswerable / Out-of-Scope / Guardrail)**:
   - Queries attempting security exploits (SQL injection, jailbreaks), requesting real-time financial market data (live stock tickers), or private personal identification (personal cell numbers / home addresses).
   - Action: Role C returns refusal/limitation message immediately without invoking services.

---

## 5. Contract Notes & Alignment Rules

1. **Exact JSON Shapes**: Committed into `contract_fixtures.json`. All team members must test against these fixtures.
2. **Day 1 Mocks**: Both endpoints have standalone mocks implemented in `mock_services.py` so Role C can build and test the full orchestrator pipeline on Day 1 without blocking on Role A or B deployments.
3. **Critical Flags (`no_match` and `answerable`)**:
   - If Role A returns `no_match: true`: The system strictly states *"I do not know / No matching company policy found"* instead of hallucinating.
   - If Role B returns `answerable: false`: The system explains that the database schema cannot answer the question and triggers fallback.
4. **Communication Protocol**:
   - Services communicate via REST JSON HTTP endpoints or local engine function wrappers. Default ports:
     - Role A (Knowledge Service): `http://127.0.0.1:8000`
     - Role B (Data Service): `http://127.0.0.1:8001`
     - Role C (Orchestrator & Chat): `http://127.0.0.1:8002`
