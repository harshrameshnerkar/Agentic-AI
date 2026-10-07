# Day 4 — Session 3: Multi-Step Tool Use & History Management

---

## 🧭 Executive Summary & Learning Goals

In Sessions 1 and 2, we learned how LLMs declare tool schemas and how to construct robust, validated tools that return errors as observations. 

In **Session 3**, we scale from isolated, single-turn tool calls to **Autonomous Multi-Step Tool Chaining**—where an AI agent autonomously plans, executes, observes, and chains multiple tools across multiple turns to solve complex, multi-domain tasks.

---

## 🎯 Syllabus & Key Concepts Covered

1. **Chaining Tool Calls**:
   - The output of Tool A (e.g. employee salary from a database) serves as the input or decision premise for Tool B (e.g. reading a compensation policy) and Tool C (calculating bonuses with arithmetic certainty).
2. **Passing Results Back into Context**:
   - The protocol of the `tool` role message: matching `tool_call_id`, role ordering invariants, and structured JSON observation ingestion.
3. **Conversation History Management**:
   - Managing the multi-turn state buffer across turns (`system` $\rightarrow$ `user` $\rightarrow$ `assistant [tool_calls]` $\rightarrow$ `tool [results]` $\rightarrow$ `assistant [answer]`).
4. **Token Growth Dynamics**:
   - Understanding how verbose tool payloads (database tables, long file passages) rapidly expand the context window and trigger exponential latency and compute costs.
5. **When to Summarise History (Context Compaction)**:
   - Defining explicit policies (token budget thresholds and step counts) to compress older intermediate tool steps into high-density executive summaries while keeping system prompts and recent context intact.
6. **Task**:
   - Run a complex business query requiring **3 tools in sequence** (`query_database` $\rightarrow$ `read_file` $\rightarrow$ `calculator` $\rightarrow$ `send_email`) and generate a turn-by-turn audit log of every step in the loop.

---

## 🏗️ Architecture: The Multi-Step Autonomous Loop

```
                     ┌──────────────────────────────────────┐
                     │           User Objective             │
                     └──────────────────┬───────────────────┘
                                        ▼
    ┌────────────────────────► [History Manager] ◄─────────────────────────┐
    │                        (Message Context Buffer)                       │
    │                                   │                                  │
    │                                   ▼                                  │
    │                    ┌─────────────────────────────┐                   │
    │                    │     LLM Planning Pass       │                   │
    │                    └──────────────┬──────────────┘                   │
    │                                   │                                  │
    │                 Has Tool Call?    │    Final Answer?                 │
    │               ┌───────────────────┴───────────────────┐              │
    │               ▼                                       ▼              │
    │    ┌────────────────────┐                 ┌────────────────────┐     │
    │    │ Emit `tool_calls`  │                 │ Synthesize Final   │     │
    │    │ (name + arguments) │                 │ Grounded Response  │     │
    │    └──────────┬─────────┘                 └────────────────────┘     │
    │               │                                                      │
    │               ▼                                                      │
    │    ┌────────────────────┐                                            │
    │    │ Tool Dispatcher    │                                            │
    │    │ (Execute Locally)  │                                            │
    │    └──────────┬─────────┘                                            │
    │               │                                                      │
    │               ▼                                                      │
    │    ┌────────────────────┐                                            │
    │    │ Tool Observation   │                                            │
    │    │ (Structured JSON)  │                                            │
    │    └──────────┬─────────┘                                            │
    │               │                                                      │
    └───────────────┴──────────────────────────────────────────────────────┘
```

---

## 🧠 Deep-Dive: Core Engineering Concepts

### 1. Chaining Tool Calls
In autonomous systems, the model rarely solves problems in a single forward pass. Intermediate states must be gathered iteratively:
* **Step 1**: The model realizes it lacks employee data $\rightarrow$ calls `query_database("SELECT role, department, salary FROM employees WHERE name LIKE '%Marcus%'")`.
* **Step 2**: The host returns: `{"name": "Marcus Vance", "role": "Senior DevOps Engineer", "salary": 135000}`.
* **Step 3**: The model inspects the observation, realizes it needs the bonus percentage $\rightarrow$ calls `read_file("bonus_policy.txt")`.
* **Step 4**: The host returns the policy text indicating Engineering Senior roles receive a 12% multiplier.
* **Step 5**: The model invokes `calculator("135000 * 0.12")` $\rightarrow$ returns `16,200`.
* **Step 6**: The model dispatches `send_email("finance.payroll@enterprise.io", ...)` to finalize payroll submission.

---

### 2. Passing Results Back into Context
Every provider API enforces strict message pairing invariants:
1. When the assistant responds with `finish_reason: "tool_calls"`, the message contains an array of `tool_calls`, each with a distinct `id` (e.g. `call_abc123`).
2. The client **must** append this assistant message to history.
3. For each tool call in the array, the client executes the function locally and appends a message with:
   ```json
   {
     "role": "tool",
     "tool_call_id": "call_abc123",
     "name": "query_database",
     "content": "{\"status\": \"success\", \"salary\": 135000}"
   }
   ```
4. **Never omit `tool_call_id`**: Modern inference engines will raise a 400 Bad Request error if a tool message lacks a matching ID from the preceding assistant turn.

---

### 3. Token Growth & Compounding Latency

As an agent executes multiple steps, the context expands linearly in tokens, but **quadratic in self-attention compute ($O(N^2)$ prefill)**:

$$\text{Turn } k \text{ Context} = \text{System Prompt} + \text{User Goal} + \sum_{i=1}^{k} \left( \text{Assistant Thought}_i + \text{Tool Output}_i \right)$$

* If a database returns 25 rows (800 tokens) and a file reader returns 150 lines (1,200 tokens), by Step 3 the context exceeds 2,500 tokens.
* On Step 4, the model must re-process all 2,500 tokens just to decide the next tool call!

---

### 4. When & How to Summarise History (Context Compaction)

| Strategy | When to Trigger | How It Works | Trade-Offs |
| :--- | :--- | :--- | :--- |
| **Naive Truncation** | When hitting token limit | Drops oldest messages indiscriminately | ❌ Destructive: drops original user goal or critical system instructions. |
| **Sliding Window** | Every $K$ turns | Keeps only the last $M$ messages | ❌ Amnesia: forgets early database queries or customer IDs. |
| **Context Compaction (Recommended)** | When context exceeds token budget (e.g. $> 1500$ tokens) | Replaces older raw tool observations with an **Executive Summary**, while preserving the System Persona, Initial User Goal, and Latest 2 Turns. | ✅ Preserves factual state while slashing token footprint by 50–70%. |

---

## 📂 File Structure

```
day_04/session_3/
├── .env                  # API credentials and model configuration
├── requirements.txt      # openai, python-dotenv, tiktoken
├── enterprise.db         # Persistent SQLite database with employees & departments
├── bonus_policy.txt      # Multi-tier enterprise compensation document
├── database_setup.py     # Database seeder script
├── tools.py              # 4 Production tools (query_database, read_file, calculator, send_email)
├── schemas.py            # Standard JSON Schema definitions
├── history_manager.py    # Conversation History Manager with Token Growth & Compaction
├── multi_step_agent.py   # Autonomous multi-step tool-use engine with step logger
├── compaction_demo.py    # Standalone demonstration of Context Compaction
├── main.py               # Master walkthrough executing the 3-tool chained sequence
└── README.md             # This comprehensive educational guide
```

---

## ⚡ Execution Commands

```powershell
cd C:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_04\session_3

# 1. Initialize the SQLite database
python database_setup.py

# 2. Test Context Compaction & Token Reduction
python compaction_demo.py

# 3. Run the Master Multi-Step Chained Sequence (>= 3 tools in sequence)
python main.py
```
