# Day 4 — Session 1: Tool & Function Calling

## 1. Executive Summary & Learning Goals
Tool calling (also known as function calling) allows LLMs to transcend static parametric memory and interface with deterministic computation, live APIs, and private databases.

### Core Concepts Covered:
1. **How the Model Requests a Tool**:
   - The model does **NOT** run any code.
   - It emits structured JSON specifying `name` and `arguments`, accompanied by `finish_reason="tool_calls"`.
2. **JSON Schema Definitions**:
   - Defining tool signatures using standard JSON Schema (`type`, `properties`, `required`, `description`).
   - The critical role of semantic descriptions in guiding model decision-making.
3. **The 3-Turn Request ➔ Execute ➔ Return Loop**:
   - **Turn 1 (Request)**: Client sends prompt + schemas. Model returns `tool_calls` with unique `id`.
   - **Turn 2 (Execute)**: Python host inspects tool call, runs local code, and serializes output.
   - **Turn 3 (Return & Synthesize)**: Client sends tool message (`role: "tool"`, `tool_call_id`) back to model. Model responds with grounded natural language answer.
4. **`tool_choice` Modalities**:
   - `"auto"`: Model dynamically chooses whether to call a tool or reply directly.
   - `"none"`: Disables all tools; forces direct parametric response.
   - `"required"`: Mandates that the model must call at least one tool.
   - `{"type": "function", "function": {"name": ...}}`: Forces a specific function invocation.
5. **Why the Model Never Runs Code Itself**:
   - **Security & Sandboxing**: LLMs operate on remote GPU clusters without access to local OS, file handles, or network sockets.
   - **Determinism**: Probabilistic text prediction cannot guarantee arithmetic correctness; execution must be delegated to local deterministic runtimes.
   - **Architecture**: The LLM is the **Planner/Brain**, while the application host is the **Executor/Hands**.

---

## 2. Architecture & File Structure

```
day_04/session_1/
├── tools.py             # Pure Python function implementations (calculator, get_current_time) + registry
├── schemas.py           # Standard JSON Schema definitions matching OpenAI/Gemini specs
├── tool_caller.py       # Orchestrator running the 3-turn request -> execute -> return cycle
├── tool_choice_demo.py  # Educational comparison of auto, none, required, and forced modes
├── evaluator.py         # Automated evaluation confirming the model calls the right tool
├── main.py              # Master walkthrough tying all concepts together
├── requirements.txt     # Python dependencies
└── .env                 # API credentials and model configuration
```

---

## 3. Quickstart & Execution

```powershell
cd C:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_04\session_1

# 1. Test pure Python tools locally
python tools.py

# 2. Inspect the JSON Schemas
python schemas.py

# 3. Test the 3-Turn Tool Execution Loop
python tool_caller.py

# 4. Compare tool_choice modes (auto vs none vs required)
python tool_choice_demo.py

# 5. Run the Automated Tool Routing Evaluation
python evaluator.py

# 6. Run the Full Walkthrough
python main.py
```
