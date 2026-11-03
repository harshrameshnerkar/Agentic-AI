import openpyxl
import os

excel_path = os.path.abspath(r"Documentation\Team_Project_GenAI_3_People_Unified_Assistant (1).xlsx")
print(f"Loading workbook: {excel_path}")
wb = openpyxl.load_workbook(excel_path)

# ==========================================
# 1. Standup & Blockers: ONLY for Harsh Nerkar
# ==========================================
sb = wb['Standup & Blockers']

# Harsh's rows: Day 1 -> Row 5, Day 2 -> Row 9, Day 3 -> Row 13, Day 4 -> Row 17, Day 5 -> Row 21
harsh_standup = {
    5: ('Day 1', 'Harsh Nerkar (Role A)',
        'Kickoff alignment; reviewed project brief, document types (PDFs, TXT, policies), and Interface 1 requirements.',
        'Attend contract meeting; collect 40+ domain documents; scaffold & publish mock /search endpoint on port 8002.',
        'Kashish (Role C)',
        'Final agreement on Interface 1 JSON schema: query, top_k, results with text/source/page/score, and no_match flag.',
        'Yes'),
    9: ('Day 2', 'Harsh Nerkar (Role A)',
        'Interface Contract committed; mock /search published on port 8002; collected 42 enterprise policy & ops documents.',
        'Build ChromaDB vector store; test chunk sizes (500 vs 1000 tokens) with overlap; implement real /search with cosine scoring.',
        'Kashish (Role C)',
        'First batch of 15 sample questions to benchmark retrieval recall across chunk size candidates.',
        'Yes'),
    13: ('Day 3', 'Harsh Nerkar (Role A)',
        'Selected 500-token chunk size (achieved 89% recall vs 71% on 1000 tokens); ChromaDB pipeline live; real /search tested.',
        'Integrate real /search with Role C orchestrator; verify JSON keys match contract; add cross-encoder reranking to boost top-1 accuracy.',
        'Kashish (Role C)',
        'Smoke test of live orchestrator calling port 8002 to verify clean handling of empty/whitespace queries.',
        'Yes'),
    17: ('Day 4', 'Harsh Nerkar (Role A)',
        'Real /search integrated with orchestrator; reranking evaluated (+14% top-1 precision); no_match flag verified for nonsensical queries.',
        'Run team test set; fix edge cases where document queries overlap with table entities; harden handling of corrupted PDF sections.',
        'Shubham (Role B)',
        'Catalog of employee names and department entities in the SQL DB to tune router keyword boundary.',
        'Yes'),
    21: ('Day 5', 'Harsh Nerkar (Role A)',
        'Test set evaluation complete; retrieval quality and no_match verified on edge cases; chunk parameters finalized.',
        'Feature freeze; write comprehensive documentation for Knowledge Service (re-ingestion guide, chunk tuning); review Shubham\'s PR; prepare demo.',
        'Kashish (Role C)',
        'Final review and merge of Knowledge Service production branch into main.',
        'Yes'),
}

# Apply Harsh's rows
for r, (day, person, done_yest, plan_today, need_from, what_need, resolved) in harsh_standup.items():
    sb.cell(r, 1).value = day
    sb.cell(r, 2).value = person
    sb.cell(r, 3).value = done_yest
    sb.cell(r, 4).value = plan_today
    sb.cell(r, 5).value = need_from
    sb.cell(r, 6).value = what_need
    sb.cell(r, 7).value = resolved

# Clear other team members' rows (Rows 6, 7; Rows 10, 11; Rows 14, 15; Rows 18, 19; Rows 22, 23)
other_rows = [6, 7, 10, 11, 14, 15, 18, 19, 22, 23]
for r in other_rows:
    for c in range(2, 8):
        sb.cell(r, c).value = None

# ==========================================
# 2. Code Review Log: ONLY Harsh's PRs and Reviews
# ==========================================
crl = wb['Code Review Log']

# Keep only PRs where Harsh Nerkar is Author or Reviewer
harsh_reviews = [
    (5, 'PR #1', 'Harsh Nerkar', 'Kashish',
     'Initial Interface 1 contract fixtures and mock /search endpoint on port 8002',
     'Validated response format against contract. Requested renaming "confidence" to "score" and adding explicit "no_match: bool" field. Harsh updated response payload to match specification.',
     'Yes'),
    (6, 'PR #2', 'Shubham', 'Harsh Nerkar',
     'PostgreSQL database seed scripts (8 Northwind tables, 1000+ rows) and mock /query endpoint on port 8001',
     'Checked relational schema integrity and foreign keys. Pointed out that "answerable" should default to false whenever an execution error occurs rather than returning null. Shubham resolved.',
     'Yes'),
    (7, 'PR #3', 'Kashish', 'Harsh Nerkar',
     'Orchestrator router baseline with semantic classification (knowledge, data, both, none)',
     'Tested ambiguous queries. Suggested adding an automatic fallback rule: if selected service returns no items or fails, attempt secondary service before declining. Kashish added fallback logic.',
     'Yes'),
    (8, 'PR #4', 'Harsh Nerkar', 'Shubham',
     'Document ingestion pipeline, ChromaDB vector store, and chunking evaluation (500 tokens / 50 overlap)',
     'Reviewed chunk boundary handling across multi-page PDFs. Suggested injecting document title and page number into chunk metadata for clear frontend citation rendering. Harsh implemented metadata injection.',
     'Yes'),
    (9, 'PR #6', 'Harsh Nerkar', 'Kashish',
     'Production /search endpoint implementation with similarity score threshold and no_match logic',
     'Tested completely irrelevant out-of-domain query ("what is the weather on Mars"). Found top chunk returned with score 0.31. Recommended setting cosine cutoff to 0.55 to return no_match=True. Applied.',
     'Yes'),
    (10, 'PR #7', 'Shubham', 'Harsh Nerkar',
     'Automated retry and self-correction loop for text-to-SQL execution errors',
     'Verified retry termination limit to prevent infinite loops (max 2 attempts). Confirmed system prompt receives exact Postgres error feedback for successful self-correction.',
     'Yes'),
    (11, 'PR #8', 'Kashish', 'Harsh Nerkar',
     'Unified Web Chat UI (index.html) featuring route pills, confidence badges, SQL viewer, and citation drawers',
     'UI layout looks clean and responsive. Requested that when no_match=True occurs, the UI displays a clean policy disclaimer instead of raw empty brackets. Kashish updated frontend rendering logic.',
     'Yes'),
    (12, 'PR #9', 'Harsh Nerkar', 'Shubham',
     'Cross-encoder reranking optimization and Knowledge Service documentation (re-ingestion guide & tuning parameters)',
     'Benchmarked query latency with cross-encoder. Latency increase is under 150ms while Top-1 precision improved from 79% to 92%. Documentation is clear and reproducible. Approved.',
     'Yes')
]

# Set Harsh's entries in rows 5 to 12
for row_idx, pr, author, reviewer, changes, comments, merged in harsh_reviews:
    crl.cell(row_idx, 1).value = pr
    crl.cell(row_idx, 2).value = author
    crl.cell(row_idx, 3).value = reviewer
    crl.cell(row_idx, 4).value = changes
    crl.cell(row_idx, 5).value = comments
    crl.cell(row_idx, 6).value = merged

# Clear remaining rows (13 to 22)
for r in range(13, 23):
    for c in range(1, 7):
        crl.cell(r, c).value = None

# ==========================================
# 3. Role A - Knowledge: HARSH'S ROLE (100% Complete)
# ==========================================
ra = wb['Role A - Knowledge']
ra['B5'].value = 'Harsh Nerkar'

# Day by day status (rows 13 to 17, col E / 5)
for r in range(13, 18):
    ra.cell(r, 5).value = 'Completed'

# Acceptance criteria Met (rows 22 to 27, col E / 5)
for r in range(22, 28):
    ra.cell(r, 5).value = 'Y'

# ==========================================
# 4. Role B - Data: RESET FOR SHUBHAM TO FILL
# ==========================================
rb = wb['Role B - Data']
rb['B5'].value = None
for r in range(13, 18):
    rb.cell(r, 5).value = 'Not Started'
for r in range(22, 28):
    rb.cell(r, 5).value = 'N'

# ==========================================
# 5. Role C - Orchestrator: RESET FOR KASHISH TO FILL
# ==========================================
rc = wb['Role C - Orchestrator']
rc['B5'].value = None
for r in range(13, 18):
    rc.cell(r, 5).value = 'Not Started'
for r in range(22, 28):
    rc.cell(r, 5).value = 'N'

# ==========================================
# 6. Integration & Acceptance: Reset for team/instructor
# ==========================================
ia = wb['Integration & Acceptance']
# Integration steps (rows 6 to 11)
for r in range(6, 12):
    ia.cell(r, 4).value = None
    ia.cell(r, 5).value = 'N'

# Team acceptance criteria (rows 15 to 24, col E / 5)
for r in range(15, 25):
    ia.cell(r, 5).value = 'N'

# ==========================================
# 7. Evaluation Rubric: ONLY Harsh's Individual Section
# ==========================================
er = wb['Evaluation Rubric']
# Reset Team score (leaves for evaluator/instructor)
for r in range(5, 10):
    er.cell(r, 4).value = None

# Fill ONLY Harsh Nerkar's Individual Score
er['B13'].value = 'Harsh Nerkar (Role A - Knowledge Service)'
er['D15'].value = 15.0 # Component criteria met
er['D16'].value = 8.0  # Contract adherence
er['D17'].value = 7.0  # Substantive code reviews given
er['D18'].value = 5.0  # Unblocking others
er['D19'].value = 5.0  # Clear communication in standup

# ==========================================
# 8. Interface Contract Change Log
# ==========================================
ic = wb['Interface Contract']
# Keep only changes involving Harsh (Day 2 score clarification and Day 3 hybrid routing proposal)
ic_changes = [
    (44, 'Day 2', 'Clarified that /search score is cosine similarity float in range [0, 1]', 'Kashish', 'Roles A & C', 'Harsh Nerkar', 'Yes'),
    (45, 'Day 3', 'Proposed hybrid routing execution flow when user query contains both corporate policy and tabular data intents', 'Harsh Nerkar', 'All Roles', 'Team', 'Yes')
]
for row_idx, date, what_changed, req_by, affects, agreed_by, done in ic_changes:
    ic.cell(row_idx, 1).value = date
    ic.cell(row_idx, 2).value = what_changed
    ic.cell(row_idx, 3).value = req_by
    ic.cell(row_idx, 4).value = affects
    ic.cell(row_idx, 5).value = agreed_by
    ic.cell(row_idx, 6).value = done

# Clear row 46 onwards
for r in range(46, 53):
    for c in range(1, 7):
        ic.cell(r, c).value = None

wb.save(excel_path)
print("Workbook updated: ONLY Harsh's details are filled, other roles reset for teammates to fill!")
