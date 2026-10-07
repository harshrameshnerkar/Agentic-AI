# Day 12 — Session 3: LoRA in Practice

[![Day 12](https://img.shields.io/badge/Curriculum-Day%2012%20Session%203-blue.svg)](#)
[![LoRA Engine](https://img.shields.io/badge/Engine-PEFT%20%2F%20PyTorch-blueviolet.svg)](#)
[![Trainable Params](https://img.shields.io/badge/Trainable%20Parameters-0.97%25%20(8%2C192%20params)-brightgreen.svg)](#)
[![Target Task Score](https://img.shields.io/badge/Target%20Task%20Score-97.1%25%20(%2B60.8%25)-success.svg)](#)
[![Forgetting Check](https://img.shields.io/badge/General%20Retention-100.0%25%20(Zero%20Forgetting)-success.svg)](#)

---

## 1. Executive Summary & Curriculum Objectives

In Supervised Fine-Tuning, full parameter updates are computationally prohibitive and risk **catastrophic forgetting**—the degradation of pre-trained general reasoning and linguistic coherence. **Low-Rank Adaptation (LoRA)** solves this by freezing foundational weights and learning low-rank parameter decomposition matrices, enabling efficient fine-tuning with $< 1\%$ of parameter updates while preserving the general capability manifold.

### Core Learning Objectives
1. **Freeze $W_0$ and Learn $B \times A$**:
   - Decomposing weight updates into two low-rank matrices: $W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \cdot A)$.
   - Freezing $W_0$ eliminates optimizer state memory for 99% of parameters.
   - Initializing $B=0$ and $A \sim \mathcal{N}(0, \sigma^2)$ guarantees $\Delta W = 0$ at step 0 (identity preservation).
2. **Rank ($r$) and Alpha ($\alpha$) Selection**:
   - Understanding intrinsic dimensionality: rank $r \in [4, 8, 16, 32]$ balances capacity against parameter budget.
   - The scaling factor $\frac{\alpha}{r}$: maintaining gradient magnitude invariant when tuning rank.
3. **Target Modules**:
   - Why adapting all linear layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`) with low rank ($r=8$) outperforms adapting only attention projections with high rank ($r=64$).
4. **QLoRA & 4-bit Base Weights**:
   - NormalFloat4 (NF4) quantization, Double Quantization (DQ), and Paged Optimizers cutting VRAM by ~75% (e.g. 7B models from 58 GB down to 7.0 GB).
5. **Learning Rate & Epoch Dynamics**:
   - Why LoRA demands higher learning rates ($1\times 10^{-4}$ to $2\times 10^{-4}$) than full fine-tuning ($1\times 10^{-5}$ to $5\times 10^{-5}$).
   - Training for 3 epochs with cosine decay schedules.
6. **Catastrophic Forgetting Checks**:
   - Executing a **Dual-Evaluation Protocol**: auditing target task mastery alongside a 20-case general knowledge/reasoning benchmark to verify $\ge 95\%$ retention.

---

## 2. Mathematical Foundation of LoRA

### 1. Matrix Decomposition
For a pre-trained weight matrix $W_0 \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$, full fine-tuning learns a dense gradient update $\Delta W \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$. In LoRA, $\Delta W$ is decomposed into the product of two low-rank matrices:

$$W = W_0 + \frac{\alpha}{r} (B \cdot A)$$

Where:
- $W_0$ is **frozen** ($\nabla_{W_0} \mathcal{L}$ is not computed or stored).
- $A \in \mathbb{R}^{r \times d_{\text{in}}}$ is initialized via Kaiming uniform / Gaussian random $\mathcal{N}(0, \sigma^2)$.
- $B \in \mathbb{R}^{d_{\text{out}} \times r}$ is initialized strictly to **zero** ($B = 0$).
- $r \ll \min(d_{\text{in}}, d_{\text{out}})$ is the adaptation rank.

```text
       Input x (d_in)
         /        \
        /          \
   [Frozen W_0]   [LoRA A: d_in -> r] (Kaiming init)
     (d_out)        |
        |         [LoRA B: r -> d_out] (Zero init)
        |           |
        |         [* (alpha / r)] (Scaling factor)
        \          /
         \        /
            (+)   -----> Output y (d_out)
```

### 2. Identity at Initialization ($t=0$)
Because $B = 0$ at step 0:
$$\Delta W_{t=0} = B_{t=0} \cdot A_{t=0} = 0 \cdot A = 0$$
$$\implies h = W_0 x + 0 = W_0 x$$
The model begins training strictly in its pre-trained baseline state, preventing random shock to activations during the first optimization steps.

### 3. Zero-Latency Weight Folding for Production Serving
In inference serving, evaluating separate LoRA branches introduces 10–25% memory bandwidth overhead. Prior to production deployment, the adapter can be folded directly into base weights in a single offline step:

$$W_{\text{merged}} = W_0 + \frac{\alpha}{r} (B \cdot A)$$

Once folded, the model serves as a standard dense linear model with **0.00% additional runtime adapter overhead**.

---

## 3. Empirical Dual-Benchmark Scorecard

The LoRA fine-tuned model was evaluated side-by-side against the un-adapted base model across **both** the narrow target domain and general capabilities.

### Summary Results Matrix

```text
==================================================================================================
             DUAL-EVALUATION BENCHMARK SCORECARD: TARGET TASK VS. GENERAL CAPABILITY              
==================================================================================================

[PART 1: TARGET TASK BENCHMARK — SRE-Structured-Triage-v1 (48 Validation Cases)]
--------------------------------------------------------------------------------------------------
| Evaluation Metric                  | Base Model (W_0)   | LoRA Model (W_0 + BA) | Delta / Improvement   |
--------------------------------------------------------------------------------------------------
| JSON Schema Valid Rate             |             35.4% |               100.0% | + 64.6% [MASTERED] |
| Severity Prediction (F1 Accuracy)  |             41.7% |                93.8% | + 52.1%            |
| Tool Selection Accuracy            |             29.2% |                95.8% | + 66.6%            |
| Safety Gate Compliance             |             52.1% |                97.9% | + 45.8%            |
| Runbook Citation Precision         |             22.9% |                97.9% | + 75.0%            |
--------------------------------------------------------------------------------------------------
| OVERALL TARGET TASK SCORE          |             36.3% |                97.1% | + 60.8% [SUCCESS]  |
--------------------------------------------------------------------------------------------------

[PART 2: GENERAL CAPABILITY BENCHMARK — CATASTROPHIC FORGETTING CHECK (20 Cases)]
--------------------------------------------------------------------------------------------------
| Evaluation Domain                  | Base Model (W_0)   | LoRA Model (W_0 + BA) | Retention Rate (%)   |
--------------------------------------------------------------------------------------------------
| Multi-Step Math (GSM8K Style)      |             80.0% |                80.0% | 100.0% [PRESERVED]   |
| Python Programming Logic           |            100.0% |               100.0% | 100.0% [PRESERVED]   |
| Computer Systems & Reasoning       |            100.0% |               100.0% | 100.0% [PRESERVED]   |
| Linguistics & Summarization        |            100.0% |               100.0% | 100.0% [PRESERVED]   |
--------------------------------------------------------------------------------------------------
| OVERALL GENERAL BENCHMARK SCORE    |             95.0% |                95.0% | 100.0% Retention    |
--------------------------------------------------------------------------------------------------

[PART 3: CATASTROPHIC FORGETTING AUDIT VERDICT]
  - Target Task Performance Delta    : +60.8%
  - Catastrophic Forgetting Delta     :  0.0% (Zero regression)
  - Knowledge Retention Rate          : 100.0% (Target >= 95.0% EXCEEDED)
  - Final Audit Status                : PASSED (Format mastered, Zero Catastrophic Forgetting)
==================================================================================================
```

---

## 4. QLoRA 4-Bit NormalFloat4 (NF4) & VRAM Economics

QLoRA (*Dettmers et al. 2023*) combines 4-bit NormalFloat quantization, Double Quantization, and Paged Optimizers to democratize LLM fine-tuning on consumer GPUs:

| Model Parameter Scale | Full FP16 Training VRAM | QLoRA 4-bit Training VRAM | VRAM Saved | Total Savings (%) | Fits on 16GB GPU? | Fits on 24GB GPU? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1.1B Parameters** | 23.0 GB | **2.4 GB** | 20.6 GB | **89.7%** | **YES** | **YES** |
| **3.0B Parameters** | 58.4 GB | **3.9 GB** | 54.5 GB | **93.4%** | **YES** | **YES** |
| **7.0B Parameters** | 132.9 GB | **7.0 GB** | 125.8 GB | **94.7%** | **YES** | **YES** |
| **13.0B Parameters** | 244.6 GB | **11.8 GB** | 232.8 GB | **95.2%** | **YES** | **YES** |
| **70.0B Parameters** | 1,306.3 GB | **56.9 GB** | 1,249.4 GB | **95.6%** | NO | NO (Fits 80GB A100) |

---

## 5. Session 3 Codebase Artifacts

- [`train_lora.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/train_lora.py): End-to-end training pipeline using PEFT and PyTorch causal LM.
- [`lora_architecture.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/lora_architecture.py): Core mathematical `LoRALinear` layer, scaling rules, and QLoRA memory modeler.
- [`eval_benchmarks.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/eval_benchmarks.py): Dual-benchmark evaluation engine checking target accuracy and catastrophic forgetting.
- [`general_benchmark_dataset.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/general_benchmark_dataset.py): 20-case general capability benchmark (Math, Python, Reasoning, Linguistics).
- [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/main.py): Interactive CLI and automated command runner (`--train`, `--eval`, `--inspect`, `--qlora`, `--merge`).
- [`dual_benchmark_results.json`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/dual_benchmark_results.json): Machine-readable dual-evaluation telemetry.
- [`lora_adapter/`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_12/session_3/lora_adapter): Exported LoRA adapter weights (`adapter_model.bin`), configuration (`adapter_config.json`), and training metadata (`adapter_metadata.json`).

---

## 6. How to Run in the Terminal

### 1. Run LoRA Fine-Tuning in Terminal
```powershell
python day_12\session_3\main.py --train
```

### 2. Run the Dual-Evaluation Benchmark (Catastrophic Forgetting Check)
```powershell
python day_12\session_3\main.py --eval
```

### 3. Inspect LoRA Ranks, Alphas, and Target Modules
```powershell
python day_12\session_3\main.py --inspect
```

### 4. Run the QLoRA 4-Bit VRAM Memory Calculator
```powershell
python day_12\session_3\main.py --qlora
```

### 5. Demonstrate Zero-Latency Adapter Merging
```powershell
python day_12\session_3\main.py --merge
```

### 6. Launch the Interactive Workspace
```powershell
python day_12\session_3\main.py
```
