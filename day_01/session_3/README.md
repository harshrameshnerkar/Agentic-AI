# Day 1 — Session 3: Generation Parameters & Control

---

## 🧭 Executive Summary
In this session, we master the control dials of Large Language Models: **Temperature, Top-P, Max Tokens, Stop Sequences, Message Roles, Streaming, and Determinism Seeds**. We run an empirical experiment testing the exact same prompt at temperatures `0.0`, `0.7`, and `1.2` to observe how probability sampling alters machine creativity.

---

## 1. Temperature: The Randomness Dial

### The Mathematical Reality
Before generating the next token, the model calculates raw unnormalized prediction scores (**logits** $z_1, z_2, \dots, z_V$) for every word in its vocabulary. 
Before applying the Softmax function, logits are divided by the **Temperature ($T$)**:

$$P(t_i) = \frac{\exp(z_i / T)}{\sum_{j} \exp(z_j / T)}$$

### What Happens as Temperature Changes?

```text
Low Temp (T = 0.0 to 0.2)           Medium Temp (T = 0.7)           High Temp (T = 1.2+)
      Probability                         Probability                     Probability
         |     |                             |   |                           |   | | | |
         |  █  |                             | █ █ |                         | █ █ █ █ █
         |__█__|________                     |_█_█_█________                 |_█_█_█_█_█____
        "HotReload"                         "HotReload" / "Ctrl+Brew"       "CaffeineByte", etc.
  (Sharp peak, greedy choice)             (Balanced natural distribution)      (Flat, high entropy)
```

| Temperature | Behavior | Typical Use Cases |
|---|---|---|
| **$T = 0.0$** | **Greedy / Argmax**: The highest probability token wins every time. Zero creativity, maximum reproducibility. | Code generation, SQL queries, JSON/data extraction, classification, math. |
| **$T = 0.7$** | **Balanced**: Selects likely tokens with natural, human-like linguistic variety. | General chat assistants, blog writing, documentation, customer support. |
| **$T = 1.2$** | **High Entropy / Creative**: Flattens probabilities; lower-ranked tokens get picked often. | Brainstorming brand names, poetry, roleplay, creative storytelling. |
| **$T > 1.5$** | **Chaotic**: Probabilities approach a uniform distribution; output quickly devolves into grammatical gibberish. | Experimental synthetic data generation. |

---

## 2. Top-P (Nucleus Sampling)

### How Top-P Works
Instead of picking from the entire vocabulary, **Top-P cuts off the "long tail" of low-probability words**:
1. Sort all tokens by probability in descending order.
2. Sum the probabilities starting from the top.
3. Once the cumulative sum reaches threshold $p$ (e.g., $p = 0.90$), all remaining tokens are discarded.
4. The model only samples from this high-confidence "nucleus".

### Temperature vs. Top-P
* **Temperature** changes the *steepness* of the curve across all tokens.
* **Top-P** draws a *vertical cutoff wall* that drops the least likely tokens.
* **Industry Best Practice**: **Tune Temperature OR Top-P, never both at the same time.** If you tune Temperature, keep `top_p = 1.0` (or `0.95`).

---

## 3. Max Tokens (`max_tokens` / `max_completion_tokens`)

* Sets a **hard cap** on the number of generated tokens in the response.
* If the model hits this cap before completing its sentence, it immediately stops and sets:
  ```json
  "finish_reason": "length"
  ```
* **Critical Trap with Reasoning Models**: In newer reasoning models (e.g. Gemini 3 / OpenAI o1), **internal thinking/scratchpad tokens count toward `max_tokens`**. If your `max_tokens` is set too low (e.g., 100), the model may spend all 100 tokens thinking and emit an empty final answer! Always allocate at least 500–1000 tokens when using reasoning models.

---

## 4. Stop Sequences (`stop`)

* You can provide up to 4 strings that act as an **emergency brake**:
  ```python
  stop=["\n\n", "User:", "###", "END"]
  ```
* As soon as the model generates the stop string:
  1. Generation halts immediately.
  2. The finish reason is set to `"finish_reason": "stop"`.
  3. The stop sequence itself is excluded from the returned text.
* **Why this matters for Agents**: Essential for tool-calling loops, preventing run-on sentences, and keeping few-shot chat history from hallucinating fake user turns.

---

## 5. System vs User vs Assistant Roles

```python
messages = [
    {"role": "system", "content": "You are a senior cybersecurity auditor. Respond only in markdown checklists."},
    {"role": "user", "content": "Review this firewall rule: allow tcp port 22 from 0.0.0.0/0"},
    {"role": "assistant", "content": "- [ ] **Critical Risk**: Port 22 (SSH) is open to the public internet."},
    {"role": "user", "content": "How do I restrict it to my office IP 192.168.1.100?"}
]
```

| Role | Purpose | Authority & Behavior |
|---|---|---|
| **`system`** | Sets global identity, constraints, tone, formatting rules, and guardrails. | High attention weighting; overrides user instructions when configured properly. |
| **`user`** | The instructions, questions, or data provided by the human end-user. | Dynamic, turn-by-turn input. |
| **`assistant`** | Past responses generated by the LLM. | Injects conversation history for multi-turn memory or few-shot demonstration examples. |

---

## 6. Streaming Responses (`stream=True`)

* **Without Streaming**: The client waits over HTTP until the entire response finishes generating (e.g., 8 seconds of blank screen).
* **With Streaming**: The server opens a **Server-Sent Events (SSE)** connection and emits tokens chunk-by-chunk in real time:
  ```python
  response = client.chat.completions.create(
      model="gemini-3.5-flash",
      messages=[{"role": "user", "content": "Write a poem"}],
      stream=True
  )

  for chunk in response:
      token = chunk.choices[0].delta.content
      if token:
          print(token, end="", flush=True)
  ```
* **Key Metric**: **Time-To-First-Token (TTFT)**. Users perceive the app as 10x faster because text begins rendering within 300ms.

---

## 7. Seeds & Why LLMs Aren't 100% Deterministic

You can pass an integer seed (e.g., `seed=42`) to encourage identical outputs across identical prompts. However, **LLMs are rarely 100% deterministic even at $T = 0$**.

### Why?
1. **GPU Floating-Point Non-Associativity**: Parallel CUDA threads perform floating-point additions in non-deterministic orders:
   $$(A + B) + C \ne A + (B + C) \quad \text{in 16-bit floating point arithmetic}$$
   Tiny micro-precision fluctuations alter the logits of close runner-up tokens.
2. **Mixture-of-Experts (MoE) Routing**: Different tokens in the same request may be routed across different GPU worker nodes depending on network load.
3. **Speculative Decoding**: Production APIs use small draft models to guess tokens in parallel; if a draft token is rejected due to timing thresholds, output paths can diverge.

---

## 8. Empirical Experiment: Results from [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_01/session_3/main.py)

**Prompt Tested**: `"Explain Agentic AI in 5 sentences and give one real-world example."`

```text
============================================================
TEMPERATURE EXPERIMENT
============================================================

TEMPERATURE = 0
------------------------------------------------------------
Agentic AI refers to autonomous artificial intelligence systems capable of setting goals, making decisions, and executing multi-step workflows without constant human intervention. Unlike traditional AI that simply responds to prompts, agentic systems use planning, memory, and specialized tools to solve complex problems dynamically. They can reason through obstacles, correct their own mistakes, and adapt their strategies as new information becomes available. This paradigm shifts AI from a passive assistant to an active, goal-driven worker. Ultimately, it enables software to autonomously manage intricate processes from end to end.

Real-world Example:
An autonomous software engineering agent (like Devin) can receive a prompt to fix a bug in a codebase, independently search the files, write and test the patch, and submit a pull request on GitHub without human intervention.

TEMPERATURE = 0.7
------------------------------------------------------------
Agentic AI refers to advanced artificial intelligence systems designed to autonomously perceive their environment, make decisions, and take multi-step actions to achieve specific, high-level goals. Unlike traditional AI that merely responds to single prompts, these agents can plan, use tools, learn from outcomes, and adapt without constant human intervention. They leverage Large Language Models (LLMs) as their "brain" to reason through complex problems and execute workflows across different applications. By chaining thoughts and actions together, they shift AI from a passive assistant to an active, goal-driven worker. This capability represents a major paradigm shift toward software that can independently manage and solve open-ended tasks.

Real-World Example:
An AI-powered software engineering agent (like Devin or GitHub Copilot Workspace) takes a user's feature request, browses the existing codebase, writes the necessary code, tests it locally, debugs its own errors, and submits a pull request on GitHub—all independently.

TEMPERATURE = 1.2
------------------------------------------------------------
Agentic AI refers to advanced artificial intelligence systems designed to autonomously plan, use tools, and execute multi-step workflows to achieve a specific goal with minimal human intervention. Unlike traditional AI that simply responds to prompts, agentic systems can reason, self-correct, and adapt their strategies based on outcomes. They often combine Large Language Models (LLMs) with memory modules and external software integrations to act as digital workers. This paradigm shift moves AI from a passive assistant to an active problem-solver capable of managing complex, open-ended tasks. Ultimately, it represents the frontier of automation, where software can reason through ambiguity and execute end-to-end business processes.

Real-world Example:
An AI software-engineering agent (like Devin or GitHub Copilot Workspace) can take a vague user prompt like "fix this security vulnerability in the authentication module," independently explore the codebase, write and test the patch, and submit a pull request—handling the entire multi-step debugging lifecycle on its own.
```

### Analysis of Output Changes:
1. **At $T = 0.0$ (Deterministic / Direct)**:
   * Concise, structured, and foundational definitions (*"capable of setting goals, making decisions..."*).
2. **At $T = 0.7$ (Balanced / Nuanced)**:
   * Introduces richer architectural terminology (*"perceive their environment"*, *"chaining thoughts and actions"*).
3. **At $T = 1.2$ (Creative / Frontier Framing)**:
   * Explores broader thematic phrases (*"frontier of automation"*, *"reason through ambiguity and execute end-to-end business processes"*).

---

## 9. How to Run the Code


```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_01\session_3
python main.py
```
