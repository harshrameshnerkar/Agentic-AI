# UNIFIED BUSINESS ASSISTANT

## Master Architecture & Team Study Guide

**Proposed filename:** `UNIFIED-BUSINESS-ASSISTAN.md`
**Purpose:** One shared reference for the three-person team working on
the Unified Business Assistant.
**Status:** Architecture and implementation plan --- not a claim that
the repository has been inspected or these components already exist.

------------------------------------------------------------------------

## 1. Project overview

The Unified Business Assistant brings together two independent
specialist services behind one orchestrator and user interface:

-   **Role A - Knowledge Service:** answers questions from documents
    and returns ranked passages with source and page information.
-   **Role B - Data Service:** answers questions about structured data
    by generating, validating, and safely executing read-only SQL.
-   **Role C - Orchestrator, UI & Evaluation:** decides which service
    or services to call, composes the response, displays results, and
    measures quality.

The goal is to allow a user to ask a business question in natural
language and receive an answer supported by document evidence, database
results, or a clarification when the question cannot safely or reliably
be answered.

### End-to-end conceptual flow

                         User question
                               |
                               v
                      Chat UI / Orchestrator
                               |
                               v
                         Routing engine
                         /            \
              Knowledge question    Data question
                      |                   |
                      v                   v
               Role A /search       Role B /query
                      |                   |
                      v                   v
              Ranked passages       Rows + columns
              + source + page       + SQL + answerable
                      \                   /
                       \                 /
                        v               v
                         Answer composer
                                |
                                v
                     Answer + sources + route
                                |
                                v
                              User

A combined question may call both services only when the agreed routing
policy says both are needed. Role C must not bypass Role B's SQL safety
controls.

------------------------------------------------------------------------

## 2. Ownership and boundaries

  ------------------------------------------------------------------------
  Role              Owns               Provides          Depends on
  ----------------- ------------------ ----------------- -----------------
  **A --- Knowledge Document           Ranked passages,  No other role
  Service**         ingestion,         source file,      
                    extraction/OCR,    page, score,      
                    chunking,          `no_match`        
                    embeddings, vector                   
                    index, retrieval,                    
                    `/search`                            

  **B --- Data      Database/schema,   Rows, columns,    No other role
  Service**         text-to-SQL, SQL   generated SQL,    
                    validation,        `answerable`,     
                    read-only          structured error  
                    execution,                           
                    correction loop,                     
                    `/query`                             

  **C ---           Canonical          Unified user      A and B APIs;
  Orchestrator, UI  interface          response, route   mocks are
  & Evaluation**    contract, routing, decision,         sufficient
                    HTTP clients,      evaluation report initially
                    answer                               
                    composition, UI,                     
                    shared test set                      
                    and evaluation                       
  ------------------------------------------------------------------------

### Ownership rules

1.  Role C maintains the canonical shared interface contract.
2.  Roles A and B implement their endpoints against that contract.
3.  Roles A and B must not import each other's internal Python modules.
4.  Role C calls A and B through their HTTP APIs, not by importing
    service internals.
5.  Each role owns its implementation details and role-specific tests.
6.  Shared contract changes must be logged, reviewed by affected owners,
    and tested.
7.  Shared files such as dependency manifests, environment templates,
    entry points, and deployment configuration require coordination.
8.  Do not claim a role or feature is complete until its acceptance
    criteria and tests have been verified.

------------------------------------------------------------------------

# 3. Role A --- Knowledge Service

## 3.1 Mission

Provide reliable document retrieval through `POST /search`. The service
discovers and ingests documents, extracts their text, preserves page
provenance, creates chunks and embeddings, indexes them, and retrieves
relevant passages for a query.

## 3.2 Proposed architecture

``` text
Document sources
      |
      v
Ingestion layer
  - file discovery
  - format detection
  - text extraction
  - OCR for scanned pages
  - parsing validation
      |
      v
Processing layer
  - text normalization
  - page-aware chunking
  - metadata and content hashes
      |
      v
Indexing layer
  - embeddings
  - vector index
      |
      v
Retrieval layer
  - query embedding
  - candidate retrieval
  - optional reranking
  - relevance filtering
      |
      v
POST /search
      |
      v
Ranked passages + source file + page + score + no_match
```

### Proposed folder layout

``` text
knowledge_service/
  api/
  ingestion/
  processing/
  retrieval/
  schemas/
  config/
tests/
data/
docs/
```

This is a proposal, not a verified listing of the existing repository.
Adapt it to the repository's actual structure before implementation.

## 3.3 Responsibilities and pipeline

1.  Collect and inspect at least **40 real documents**.
2.  Identify supported file types and determine which documents require
    OCR.
3.  Extract text and retain source file and page information.
4.  Normalize extracted text without losing useful meaning or
    provenance.
5.  Chunk documents and attach metadata such as document ID, filename,
    page range, and chunk index.
6.  Generate embeddings and build the vector index.
7.  Retrieve candidate chunks for each user query.
8.  Test at least two chunk sizes against the team's shared questions
    and select one based on measured results.
9.  Evaluate whether reranking improves retrieval. Keep it only if
    evidence supports the added complexity.
10. Return `no_match=true` when no relevant passage is found; a no-match
    is not the same as a service failure.
11. Support repeatable re-ingestion and avoid duplicate records where
    possible through stable IDs/content hashes.
12. Document score interpretation. A retrieval score must not be
    described as a probability unless it has been calibrated.

## 3.4 API contract concept

**Endpoint:** `POST /search`

Example request shape (final field names must be confirmed in the shared
contract):

``` json
{
  "question": "What is the company's leave policy?"
}
```

Example response shape:

``` json
{
  "results": [
    {
      "text": "Relevant passage text...",
      "source_file": "leave_policy.pdf",
      "page": 4,
      "score": 0.82,
      "chunk_id": "chunk-001"
    }
  ],
  "no_match": false
}
```

The values above are illustrative, not real search output. The team must
agree on exact field names, data types, result ordering, score
semantics, page numbering, and error format before implementation.

### Important behavior

-   The Day 1 mock must return **three hardcoded results** in the exact
    agreed response shape.
-   The real service must replace the mock without requiring Role C to
    change its consumer logic.
-   Empty or irrelevant retrieval results should be represented with the
    agreed `no_match` behavior.
-   Parsing/OCR errors must be distinguished from a valid search that
    finds no relevant content.
-   Page numbering should be consistent and documented.
-   Missing or malformed metadata should be handled explicitly rather
    than silently inventing provenance.

## 3.5 Five-day plan

### Day 1 --- Contract and documents

-   Attend the contract meeting.
-   Collect at least 40 real documents and inspect their formats and
    quality.
-   Publish and commit the mock `/search` endpoint with three hardcoded
    results.
-   Begin loading, text extraction, and scanned-page/OCR handling.

**Deliverable:** committed mock endpoint; document collection inspected.

### Day 2 --- Real retrieval

-   Implement the ingestion, extraction, chunking, embedding, and
    vector-index pipeline.
-   Test two chunk sizes on shared team questions.
-   Record the retrieval metric and explain the chosen chunk size.

**Deliverable:** working real `/search` and a measured retrieval result.

### Day 3 --- Integration and reranking

-   Replace the mock with the real service behind the same contract.
-   Fix response mismatches on Role A's side.
-   Add reranking as an experiment and measure whether it helps.

**Deliverable:** real service integrated; reranking retained or dropped
based on evidence.

### Day 4 --- Failure handling

-   Investigate failed retrieval questions.
-   Improve handling of no relevant results, parsing errors, and
    questions requiring database facts rather than documents.
-   Re-check `no_match` behavior.

**Deliverable:** improved retrieval results and tested no-match
behavior.

### Day 5 --- Documentation and demo

-   Document re-ingestion, chunk-size choice, score range/meaning, and
    known limitations.
-   Review a teammate's pull request.
-   Prepare the demo.

**Deliverable:** documentation, PR review, demo-ready service.

## 3.6 Role A tests and acceptance checks

-   Extraction tests for supported document types.
-   Tests for scanned documents/OCR where relevant.
-   Chunk metadata preserves the source and page.
-   Re-ingestion does not create unintended duplicates.
-   `/search` matches the contract for both results and no-match cases.
-   Compare chunk sizes using the shared test set.
-   Report retrieval quality with the metric and test-set size stated.
-   Measure reranking instead of assuming it helps.

------------------------------------------------------------------------

# 4. Role B --- Data Service

## 4.1 Mission

Provide safe answers to structured-data questions through `POST /query`.
The service owns the database, schema context, SQL generation,
validation, bounded read-only execution, and any correction loop.

## 4.2 Proposed architecture

``` text
Database + documented schema
            |
            v
       POST /query
            |
            v
 Request validation / request ID
            |
            v
     Schema context builder
            |
            v
       SQL generation
            |
            v
         Safety gate
  - parse generated SQL
  - allow only permitted read queries
  - reject destructive operations
  - enforce query/result limits
            |
            v
      Read-only executor
            |
            +------ success ------> rows + columns + SQL
            |
            +------ error --------> bounded correction attempt
                                       |
                                       v
                                Validate again
                                       |
                                       v
                                Safe execution only
```

### Proposed folder layout

``` text
data_service/
  api/
  database/
  sql/
  correction/
  schemas/
  tests/
data/
docs/
```

This is a proposed layout and must be reconciled with the actual
repository before implementation.

## 4.3 Database and schema requirements

1.  Build or source a realistic database with at least **five related
    tables** and **1,000 or more rows**.
2.  Document tables, columns, primary keys, foreign keys, relationships,
    and important business meanings.
3.  Seed and validate the database reproducibly.
4.  Keep the database separate from the knowledge vector index.
5.  Supply compact, relevant schema context to the model rather than
    blindly prompting with the entire database DDL.
6.  Track schema changes so SQL generation and documentation remain
    aligned.

## 4.4 SQL safety and execution

The service must generate SQL, validate it, and only then execute it.
The model must never execute SQL directly.

Safety controls should include:

-   Parse SQL with a SQL parser before execution.
-   Allow only the agreed read-only query forms.
-   Reject destructive or mutating operations such as `DROP`, `DELETE`,
    `UPDATE`, `INSERT`, `CREATE`, and `ALTER`, as applicable to the
    parser and database dialect.
-   Reject multiple statements and other prohibited constructs.
-   Execute using a read-only database connection or equivalent
    database-level restriction.
-   Apply execution timeouts, result limits, and other agreed resource
    bounds.
-   Revalidate every corrected SQL query before executing it.
-   Do not expose database credentials or unrestricted internal errors
    to the user.
-   Log enough sanitized diagnostic information to debug failures.

**Required proof:** demonstrate that destructive SQL is blocked at
validation/safety enforcement, not merely that it happens to fail during
execution.

A read-only connection is a defense-in-depth measure; it does not
replace SQL validation. The exact safety guarantees depend on the
database engine, driver, permissions, and implementation and must be
tested.

## 4.5 API contract concept

**Endpoint:** `POST /query`

Example request shape (final fields must be agreed):

``` json
{
  "question": "Which five customers have the most invoices?"
}
```

Example response shape:

``` json
{
  "columns": ["CustomerName", "InvoiceCount"],
  "rows": [
    ["Customer A", 12],
    ["Customer B", 10]
  ],
  "sql": "SELECT ...",
  "answerable": true,
  "error": null
}
```

The rows above are illustrative only. The actual response must include
the agreed error schema and row format. Do not return `answerable=true`
simply because SQL executed successfully: the result must address the
question. Conversely, a valid query returning zero rows is not
automatically unanswerable.

### Error and answerability behavior

-   Use `answerable=false` when the question cannot be answered reliably
    from the available database or needs clarification.
-   Distinguish an unanswerable question from a SQL generation error,
    validation rejection, database outage, and valid empty result.
-   Do not guess an interpretation when material ambiguity changes the
    answer.
-   If self-correction is implemented, feed back bounded and sanitized
    database error information.
-   Set a finite correction-attempt limit.
-   Validate every new attempt from the beginning.
-   Preserve a request ID and attempt number in diagnostic logs.

## 4.6 Five-day plan

### Day 1 --- Contract, database, and mock

-   Attend the contract meeting and agree on the question format with
    Role C.
-   Create or source a database with at least five related tables and at
    least 1,000 rows.
-   Document the schema.
-   Publish and commit a mock `/query` that returns two hardcoded rows
    and fake SQL in the agreed response shape.

**Deliverable:** seeded database, schema documentation, committed mock
endpoint.

### Day 2 --- Real text-to-SQL and safety

-   Build schema context.
-   Generate SQL and validate before execution.
-   Add read-only execution and result/time limits.
-   Test the shared question set.
-   Prove destructive SQL is blocked before execution.

**Deliverable:** working `/query` and demonstrable safety tests.

### Day 3 --- Self-correction and integration

-   Integrate with Role C using the same contract.
-   Add a bounded self-correction loop using sanitized DB error
    feedback.
-   Test at least three deliberately broken queries and record whether
    they self-correct.
-   Keep logs visible enough to explain each attempt.

**Deliverable:** integrated service and evidence from three correction
cases.

### Day 4 --- Failure taxonomy

Classify failures, including: - Wrong join. - Wrong aggregation. -
Hallucinated/nonexistent column. - Ambiguous question.

Fix the largest failure category first. Test that `answerable=false` is
returned correctly when the database cannot support an answer.

**Deliverable:** measured failure taxonomy and targeted improvement.

### Day 5 --- Documentation and demo

-   Document schema, how to change/reseed the database, safety controls,
    limitations, and how to run tests.
-   Review a teammate's pull request.
-   Prepare the demo.

**Deliverable:** documentation, PR review, demo-ready service.

## 4.7 Role B tests and acceptance checks

-   Database integrity and foreign-key checks.
-   Contract tests for successful, empty, unanswerable, and error cases.
-   SQL parser and safety tests for forbidden operations and multiple
    statements.
-   Tests proving validation occurs before execution.
-   Tests that corrected SQL is validated again.
-   Read-only connection, timeout, and result-limit tests.
-   Three documented self-correction test cases.
-   Failure counts by category.
-   Confirm SQL, rows, columns, `answerable`, and error fields stay
    consistent.

------------------------------------------------------------------------

# 5. Role C --- Orchestrator, UI & Evaluation

## 5.1 Mission

Role C connects the services without coupling to their internals. It
owns the shared contract, routing policy, HTTP clients, answer
composition, chat UI, evaluation harness, and top-level documentation.

Role C must start with mocks and continue development independently of
Roles A and B.

## 5.2 Proposed architecture

``` text
Chat UI
   |
   v
Orchestrator API
  - request validation
  - request ID
  - response formatting
   |
   v
Routing engine
  - knowledge question?
  - data question?
  - combined question?
  - clarification needed?
   |
   +---------------------+
   |                     |
   v                     v
Role A HTTP client    Role B HTTP client
POST /search          POST /query
   |                     |
   v                     v
Knowledge result      Data result
   |                     |
   +----------+----------+
              |
              v
        Answer composer
  - preserve sources/provenance
  - distinguish no-match and errors
  - summarize data without changing it
              |
              v
 Unified response to UI
              |
              v
 Evaluation + observability
```

### Proposed folder layout

``` text
orchestrator/
  api/
  routing/
  clients/
  composition/
  observability/
  ui/
  evals/
  contracts/
  tests/
```

This is a proposal; adapt it to the actual repository after inspecting
existing structure.

## 5.3 Routing behavior

The team must agree on routing rules before implementation. At minimum,
the router should distinguish:

-   **Knowledge questions:** policy, process, or facts expected in
    documents.
-   **Data questions:** counts, lists, aggregations, comparisons, and
    facts expected in the structured database.
-   **Combined questions:** questions that require both document
    evidence and structured data, only when the policy explicitly calls
    for both.
-   **Ambiguous questions:** questions where the intended meaning or
    data source is unclear enough that clarification is safer.
-   **Unanswerable questions:** questions unsupported by the available
    documents and/or database.

Do not force every question through both services. Do not infer that a
question is answerable solely because a service responded successfully.

For every request, record the route, reason, services called, and
request ID. If a confidence score is implemented, document what it means
and avoid treating an uncalibrated model score as a probability.

## 5.4 HTTP client and composition rules

-   Use HTTP clients for Role A and Role B; do not import their internal
    service modules.
-   Handle timeouts, unavailable services, malformed responses, and
    agreed error formats.
-   Preserve source file/page information when presenting knowledge
    answers.
-   Present SQL/data results accurately and do not invent missing
    values.
-   Keep service errors distinct from valid no-match or unanswerable
    results.
-   If a required service is unavailable, communicate the partial result
    or failure honestly according to the agreed policy.
-   Keep the UI clear about the route used and show sources when
    applicable.
-   Include loading and error states in the chat UI.

## 5.5 Shared evaluation set

Create a shared set of **40 business questions**. A proposed starting
distribution is:

  ------------------------------------------------------------------------
  Category                            Proposed count Purpose
  --------------------- ---------------------------- ---------------------
  Knowledge/document                              15 Retrieval, source
                                                     attribution, grounded
                                                     answers

  Structured data                                 15 SQL generation,
                                                     result correctness,
                                                     answerability

  Ambiguous                                        5 Clarification and
                                                     safe routing

  Unanswerable                                     5 Correct no-answer
                                                     behavior

  **Total**                                   **40** Shared team
                                                     evaluation
  ------------------------------------------------------------------------

This distribution is a proposal, not a settled requirement. The team
should confirm it and define expected route, expected answer, expected
sources, and acceptable answer variations before scoring.

Suggested fields per test case:

``` json
{
  "question_id": "Q001",
  "question": "Example business question",
  "expected_route": "knowledge",
  "expected_answer": "Expected answer or scoring criteria",
  "expected_sources": ["policy.pdf"],
  "category": "knowledge"
}
```

This is a template only. Do not treat it as a completed benchmark until
real questions, gold answers, and expected sources have been authored
and reviewed.

## 5.6 Evaluation metrics

Keep these measurements separate:

1.  **Routing accuracy:** percentage of questions sent to the expected
    route.
2.  **Retrieval quality:** a defined metric such as Recall@k on
    answerable knowledge questions.
3.  **Data answer correctness:** whether returned rows and the composed
    answer match the expected result.
4.  **Source/citation correctness:** whether cited files/pages actually
    support the answer.
5.  **Unanswerable handling:** whether unsupported questions are
    correctly declined or clarified.
6.  **End-to-end quality:** whether the final user-facing response is
    correct and grounded.
7.  **Reliability:** service errors, timeouts, malformed responses, and
    latency.

Report total questions, metric definitions, denominators, category-level
results, and failed question IDs. A 40-question project benchmark is
useful for comparison but is not proof of production reliability.

## 5.7 Five-day plan

### Day 1 --- Contract and shared test set

-   Facilitate the contract meeting.
-   Fill in and commit the Interface Contract.
-   Create the shared 40-question set with expected routing and answer
    criteria.
-   Ensure both services have mocks that match the contract.

**Deliverable:** committed contract and reviewed test set.

### Day 2 --- Orchestrator against mocks

-   Implement routing and HTTP clients.
-   Compose responses with source citations and data results.
-   Handle no-match, unanswerable, and error states.
-   Run at least one complete fake-question end-to-end path.
-   Log routing decisions for every question.

**Deliverable:** working orchestrator against mocks.

### Day 3 --- Real-service integration

-   Integrate Role A first and verify the knowledge path.
-   Integrate Role B next and verify the data path.
-   Keep the contract change log updated.
-   Start the evaluation script.

**Deliverable:** both real services integrated and initial
routing-accuracy report.

### Day 4 --- Evaluation and UI

-   Score the complete shared set.
-   Identify the largest routing-error category and fix it.
-   Build or finish the chat UI showing answers, sources when relevant,
    and route.
-   Verify loading, no-match, and service-error states.

**Deliverable:** measured full-set results and working UI.

### Day 5 --- Final documentation and demo

-   Write the top-level README covering the whole system.
-   Write the evaluation results and limitations.
-   Review both teammate pull requests.
-   Prepare and rehearse the final demo.

**Deliverable:** documented system, reviewed PRs, and demo-ready
integration.

## 5.8 Role C tests and acceptance checks

-   Contract tests for both mock and real services.
-   Unit tests for routing categories and clarification behavior.
-   HTTP client tests for timeouts, malformed data, and service
    failures.
-   Composition tests preserving sources and data values.
-   End-to-end tests using mocks and then real services.
-   Evaluation script reporting routing accuracy and separate
    answer-quality metrics.
-   UI checks for sources, route, no-match, unanswerable, loading, and
    errors.

------------------------------------------------------------------------

# 6. Canonical interface contract --- decisions to finalize

The exact contract must be agreed before implementation. This document
records the design questions; it does not silently decide unresolved
details.

## 6.1 Shared decisions

-   API hostnames, ports, and endpoint paths.
-   Request/response JSON field names and types.
-   Required and optional fields.
-   Request ID format and propagation.
-   Standard error shape and error categories.
-   Timeouts and retry rules.
-   Health/readiness endpoints, if required.
-   Environment-variable names and example configuration.
-   Local startup commands and dependency ownership.
-   Whether combined questions call both services and how partial
    results are handled.
-   Whether scores/confidence are exposed to users or only logged.
-   Page numbering conventions and result ordering.
-   Data result size limits and SQL disclosure policy.
-   Versioning policy for contract changes.

## 6.2 Example unified response concept

The final orchestrator response may use a shape conceptually like this:

``` json
{
  "answer": "User-facing answer",
  "route": "knowledge",
  "sources": [
    {
      "source_file": "example.pdf",
      "page": 2
    }
  ],
  "data": null,
  "status": "success",
  "request_id": "request-identifier"
}
```

This is an illustrative concept, not a finalized schema. The contract
must define how `sources`, `data`, `status`, partial results, errors,
and combined routes are represented.

## 6.3 Contract change process

1.  The proposing role documents the reason and exact schema change.
2.  Role C updates the canonical contract and change log.
3.  Every affected role reviews the proposed change before merging.
4.  Update mocks, schemas, and contract tests together.
5.  Run affected unit, contract, and end-to-end tests.
6.  Announce the new contract version and integration impact.

No role should silently change response fields and expect teammates to
discover the change during integration.

------------------------------------------------------------------------

# 7. Preventing team collisions

## Shared-file rules

-   Assign a clear owner to every shared file.
-   Avoid simultaneous edits to the same file where possible.
-   Coordinate changes to dependency manifests, environment templates,
    app entry points, and deployment files.
-   Do not commit secrets, API keys, credentials, or local databases
    containing sensitive information.
-   Use example environment files with placeholder variable names, not
    real secrets.
-   Agree on branch and pull-request conventions before parallel work.

## Service-boundary rules

-   Role A owns `/search`; Role B owns `/query`; Role C owns
    orchestration.
-   A and B may have separate internal dependencies and implementations.
-   C communicates through documented HTTP contracts.
-   Mocks and real services must return the same schema.
-   SQL validation is owned and enforced by B, never bypassed by C.
-   Retrieval provenance is owned by A and must be preserved by C.
-   Shared errors should have stable, documented meanings.

## Testing ownership

  -----------------------------------------------------------------------
  Test category           Primary owner           Shared responsibility
  ----------------------- ----------------------- -----------------------
  Extraction, chunking,   A                       C validates consumed
  retrieval                                       response

  SQL generation,         B                       C validates response
  validation, execution                           handling
  safety                                          

  Contract compatibility  C maintains contract    A and B run contract
                                                  tests

  Routing and composition C                       A/B provide
                                                  representative fixtures

  End-to-end integration  C coordinates           All three fix failures
                                                  in their owned
                                                  components

  Full benchmark/report   C                       A/B analyze
                                                  service-specific
                                                  failures
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 8. Shared milestone checklist

## Day 1

-   [ ] Contract agreed and committed.
-   [ ] Role A mock `/search` returns three hardcoded results in the
    agreed shape.
-   [ ] Role B mock `/query` returns two hardcoded rows and fake SQL in
    the agreed shape.
-   [ ] At least 40 real documents collected and inspected.
-   [ ] Database with at least five related tables and 1,000+ rows is
    available.
-   [ ] Shared 40-question set drafted and reviewed.
-   [ ] All roles can run their own mock-backed development path.

## Day 2

-   [ ] Role A real ingestion and retrieval pipeline works.
-   [ ] Two chunk sizes compared and a choice documented.
-   [ ] Role B real text-to-SQL path works.
-   [ ] SQL validation is shown to block destructive SQL before
    execution.
-   [ ] Role C orchestrator works with both mocks.

## Day 3

-   [ ] Role A integrated without changing the agreed contract.
-   [ ] Role B integrated without changing the agreed contract.
-   [ ] Role B has at least three documented self-correction tests.
-   [ ] Contract mismatches are fixed and logged.
-   [ ] Evaluation script has an initial report.

## Day 4

-   [ ] Role A has measured retrieval results and tested `no_match`.
-   [ ] Role B has a failure taxonomy and fixes for its largest
    category.
-   [ ] Role C reports routing accuracy separately from answer quality.
-   [ ] UI displays answers, route, relevant sources, and errors.
-   [ ] Shared test set has been run and failures are recorded.

## Day 5

-   [ ] Role A documents re-ingestion, chunk size, score semantics, and
    limitations.
-   [ ] Role B documents schema changes, database setup, and safety
    guarantees.
-   [ ] Role C writes the top-level README and evaluation results.
-   [ ] Teammate PRs are reviewed.
-   [ ] Tests pass and the demo is rehearsed.
-   [ ] Final report clearly states known limitations and unverified
    claims.

------------------------------------------------------------------------

# 9. Final acceptance criteria

The project should not be described as complete until the team can
demonstrate:

1.  A user question reaches the intended route, with routing decisions
    logged.
2.  The knowledge service returns relevant passages with usable source
    and page metadata.
3.  The data service returns accurate structured results and exposes the
    generated SQL according to the contract.
4.  Unsafe SQL is rejected before execution, with read-only execution
    and bounded resources as defense in depth.
5.  Unanswerable, ambiguous, no-match, malformed-response, timeout, and
    service-failure cases are handled distinctly.
6.  Mock services can be replaced with real services without
    consumer-code changes caused by schema drift.
7.  Contract, unit, and end-to-end tests run reproducibly.
8.  Evaluation reports include metric definitions, denominators,
    category results, and failed case IDs.
9.  Setup instructions and known limitations are documented.
10. The team can run the integrated system and explain each role's
    responsibility.

## 10. Important limitations and open decisions

-   This is a consolidated study and planning document based on the role
    descriptions supplied by the team. It is not a repository audit.
-   Folder layouts, JSON examples, question distribution, and unified
    response examples are proposals until agreed and implemented.
-   The final API contract should be settled by the team before service
    code is written.
-   Model-generated SQL and retrieval results require empirical testing;
    architecture alone does not guarantee correctness.
-   A small benchmark measures progress on that benchmark; it does not
    establish production readiness.
-   Real credentials, deployment settings, service ports, libraries,
    database engine, embedding model, vector store, and LLM provider
    must be selected or confirmed by the team.

------------------------------------------------------------------------

## Quick reference

-   **Role A:** documents → ingestion/OCR → chunking → embeddings/index
    → retrieval → `POST /search`.
-   **Role B:** database/schema → SQL generation → validation →
    read-only execution → `POST /query`.
-   **Role C:** UI → routing → HTTP clients → A/B results → grounded
    answer composition → evaluation.
-   **Contract owner:** Role C.
-   **Mock-first rule:** both mocks exist on Day 1.
-   **Safety rule:** B validates every SQL attempt before execution.
-   **Integration rule:** C uses HTTP interfaces; no cross-importing A/B
    internals.
-   **Quality rule:** measure retrieval, routing, answer correctness,
    citations, and unanswerable handling separately.
