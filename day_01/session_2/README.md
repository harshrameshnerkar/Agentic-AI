# Day 1 — Session 2: How an LLM Actually Works

---

## 🧭 Executive Summary
In this session, we peel back the abstraction of Large Language Models (LLMs) to understand their mechanical reality: **how text becomes numbers, how models predict tokens autoregressively, why hallucinations happen, and how token economics dictate real-world software costs.**

---

## 1. Tokens and Tokenization

### What is a Token?
An LLM **cannot read letters, words, or sentences**. It operates strictly on integers (Token IDs).
* A token is a **subword unit**.
* In English, **1 token ≈ 4 characters** or **0.75 words** (rule of thumb: 100 tokens ≈ 75 words).
* Common words like `"the"`, `"and"`, or `"explain"` are single tokens.
* Rare words, typos, code symbols, and non-Latin scripts are split into multiple smaller fragments.

### Byte-Pair Encoding (BPE)
Modern models (GPT-4o, Claude, Llama 3) use **Byte-Pair Encoding (BPE)**:
1. **Start with base vocabulary**: Every unique byte (256 base bytes).
2. **Iterative merging**: Count the most frequently occurring adjacent pairs of bytes in the training corpus and merge them into a new single token.
3. **Repeat** until a target vocabulary size is reached:
   - `cl100k_base` (GPT-4 / GPT-3.5): ~100,000 token vocabulary.
   - `o200k_base` (GPT-4o / GPT-4o-mini): ~200,000 token vocabulary.

### Token Inflation & Non-Latin Scripts
Notice what happens when we tokenize English vs Hindi or dense JSON:
* English: `"Explain the difference"` → 3 words = 3 tokens.
* Non-Latin script: `"नमस्ते"` → 1 word = 4 tokens (`'न'`, `'म'`, `'स्त'`, `'े'`).
* **Cost Impact**: Languages with non-Latin alphabets consume 2x to 5x more tokens for the exact same semantic meaning.

---

## 2. The Context Window

### What is the Context Window?
The **context window** is the maximum sequence length (in tokens) the model can process in a single inference pass. It is a shared container:
$$\text{Total Tokens} = \text{System Prompt} + \text{Chat History} + \text{Retrieved Docs (RAG)} + \text{User Input} + \text{Model Output}$$

### Evolution of Context Sizes
| Era | Context Window | Limitation |
|---|---|---|
| **GPT-3 (2020)** | 2,048 tokens (~1,500 words) | Barely fit 2 chat turns. |
| **GPT-4 (2023)** | 8,192 – 32,768 tokens | Moderate documents and basic RAG. |
| **GPT-4o / Claude 3.5 (2024)** | 128,000 – 200,000 tokens | Entire codebases or books (~500 pages). |
| **Gemini 1.5 / 2.5 (2024–2026)** | 1,000,000 – 2,000,000 tokens | Hours of video, massive audio, full enterprise archives. |

### The Quadratic Attention Problem ($O(N^2)$)
In standard Transformer self-attention, every token calculates attention scores against every other token in the sequence. Doubling the context length quadruples ($4\times$) the memory and compute required during the prefill phase:
$$\text{Attention Memory} \propto N^2$$
Modern architectures bypass this using:
- **FlashAttention**: Fast memory-efficient exact attention at the GPU hardware level.
- **RoPE (Rotary Position Embeddings)**: Dynamic context scaling without retraining from scratch.
- **KV Caching**: Storing computed key-value tensors in GPU VRAM to avoid recalculating past tokens on every generation step.

---

## 3. Next-Token Prediction & Sampling Mechanics

### The Core Training Objective
An LLM does not "think" or "search". It is a **next-token prediction engine**:
$$P(t_{k+1} \mid t_1, t_2, \dots, t_k)$$
Given the preceding sequence, it outputs a probability distribution over its entire vocabulary (e.g. 200,000 possible tokens).

### From Logits to Generated Text
1. **Forward Pass**: The input tokens pass through transformer layers and produce raw, unnormalized scores called **Logits** ($z_1, z_2, \dots, z_V$).
2. **Softmax**: Converts logits into probabilities:
   $$P(t_i) = \frac{e^{z_i / T}}{\sum_{j} e^{z_j / T}}$$
3. **Sampling Parameters**:
   - **Temperature ($T$)**:
     - $T \to 0$ (e.g., $0.0$ to $0.2$): Makes the distribution steep. The highest probability token wins almost every time (deterministic, ideal for code, math, and data extraction).
     - $T > 1.0$ (e.g., $1.2$ to $1.5$): Flattens the distribution, giving less probable words a chance to be chosen (creative writing, brainstorming).
   - **Top-P (Nucleus Sampling)**: Selects only the smallest set of tokens whose cumulative probability exceeds threshold $p$ (e.g., $p = 0.9$). Eliminates long-tail nonsense tokens.
   - **Top-K**: Restricts selection strictly to the top $k$ most probable tokens (e.g., $k = 40$).

---

## 4. Why Models Hallucinate

### The Illusion of Truth
* **LLMs are lossy compression models of the internet**, not relational databases or factual knowledge graphs.
* When asked a question, the model does not check facts. It completes the sentence using the most statistically plausible sequence of tokens.
* If a fictional citation or plausible-sounding fake library looks grammatically and stylistically correct in that context, the model will output it with **100% confidence**.

### Root Causes of Hallucination:
1. **Statistical Bias vs Truth**: Plausible-sounding text $\ne$ factually accurate text.
2. **Out-of-Distribution Inputs**: Asking about obscure topics where training data was scarce causes the model to fill blanks using adjacent semantic patterns.
3. **Sycophancy**: Models are trained with RLHF (Reinforcement Learning from Human Feedback) to sound polite and helpful, often agreeing with false user premises rather than correcting them.

### Engineering Mitigations:
- **Grounding with RAG (Retrieval-Augmented Generation)**: Inject verified external documents into the prompt.
- **Tool Use / Function Calling**: Force the model to query real databases and APIs rather than relying on its weights.
- **Low Temperature ($T = 0.0$)**: Eliminates random sampling fluctuations.

---

## 5. Knowledge Cutoff

### Why Can't Models Know Real-Time News?
- Models learn knowledge stored in static weights during **pre-training**.
- Once training completes, the weights are **frozen**.
- Pretraining modern frontier models costs tens of millions of dollars and takes months. You cannot "update" an LLM like you update a SQL table.
- **The Solution**: Real-time applications must provide live context via search tools, API calls, or RAG pipelines.

---

## 6. Parameters vs Capability

### What is a Parameter?
A **parameter** (weight) is a floating-point number in the neural network's matrices ($W_Q, W_K, W_V, W_{FFN}$).
- **7B Parameters** (e.g. Llama 3 8B, Gemma 7B): Can run locally on a consumer laptop/GPU (~8 GB - 16 GB VRAM).
- **70B Parameters** (e.g. Llama 3 70B): Strong enterprise reasoning, requires multi-GPU servers (2x A100/H100).
- **400B+ Parameters** (e.g. GPT-4, Llama 3 405B): Frontier reasoning, requires data center clusters.

### Quantization (Shrinking Models for Local Use)
- Full precision weights are usually stored in **16-bit floating point (FP16)**:
  $$\text{VRAM Required} \approx \text{Parameters (in Billions)} \times 2\text{ GB}$$
  *An 8B model requires $\approx 16\text{ GB}$ VRAM in FP16.*
- **Quantization** rounds weights to lower precision:
  - **INT8 (8-bit)**: Halves VRAM to $\approx 8\text{ GB}$ with negligible quality drop.
  - **INT4 (4-bit)**: Reduces VRAM to $\approx 4\text{ GB}$ (runs on MacBook Air or smartphone!).

---

## 7. Open vs Closed Models

| Feature | Closed Models (OpenAI, Anthropic, Google) | Open-Weight Models (Meta Llama, Mistral, Gemma) |
|---|---|---|
| **Access Model** | Proprietary API via HTTP | Downloadable weights (Hugging Face) |
| **Hosting & Ops** | Zero infrastructure management | Self-hosted (Ollama, vLLM, AWS, RunPod) |
| **Pricing** | Pay per token (variable cost) | Fixed GPU compute cost (server per hour) |
| **Data Privacy** | Data leaves your perimeter (unless BAA signed) | 100% on-premise / air-gapped security |
| **Fine-Tuning** | Limited / API-dependent | Complete weight access (LoRA, QLoRA, full tuning) |
| **Censorship / Guardrails** | Strict provider-enforced safety policies | Fully customizable / uncensored control |

---

## 8. Hands-on Token Counting & Cost Estimation

### The 5 Evaluated Prompts:
1. **Conversational**: Short English conceptual question (14 input tokens).
2. **Code Gen**: Python `binary_search` specification (16 input tokens).
3. **JSON Data**: Key-value extraction with punctuation (26 input tokens).
4. **Technical RAG**: Textbook excerpt on transformer self-attention (15 input tokens).
5. **Multilingual**: Hindi & English code-switched text (16 input tokens).

### Summary Table from [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_01/session_2/main.py):

| # | Category | Chars | In Tokens | Exp Out Tokens | GPT-4o-mini ($) | GPT-4o ($) |
|---|---|---|---|---|---|---|
| 1 | Conversational | 84 | 14 | 50 | $0.000032 | $0.000535 |
| 2 | Code Gen | 78 | 16 | 150 | $0.000092 | $0.001540 |
| 3 | JSON Data | 93 | 26 | 30 | $0.000022 | $0.000365 |
| 4 | Technical RAG | 103 | 15 | 100 | $0.000062 | $0.001038 |
| 5 | Multilingual | 73 | 16 | 60 | $0.000038 | $0.000640 |

### Cost Calculation Formula
$$\text{Call Cost} = \left(\frac{\text{Input Tokens} \times \text{Input Rate}}{1,000,000}\right) + \left(\frac{\text{Output Tokens} \times \text{Output Rate}}{1,000,000}\right)$$

---

## 9. How to Run the Code

From your terminal, navigate to `session_2` and run:

```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_01\session_2
python main.py
```
