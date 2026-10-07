# Day 3 - Session 1: Embeddings, Vector Similarity & Failure Modes

Welcome to **Day 3: Embeddings, Vector DB & RAG**!

In **Session 1**, we dive into the mathematical foundation of modern AI retrieval: **Vector Embeddings**, **Cosine Similarity vs. Euclidean Distance**, **Semantic Search in NumPy**, and **Inspecting Where Embeddings Fail (The Negation Trap)**.

---

## 🎯 What You Will Learn

1. **What an Embedding Is**:
   - Converting unstructured human language into a dense vector of floating-point numbers in a high-dimensional continuous space ($\mathbb{R}^d$).
2. **Dimensions**:
   - What dimensionality means (e.g. 384, 1536, 3072) and the trade-offs between memory footprint, inference latency, and semantic resolution.
3. **Cosine Similarity vs. Euclidean Distance**:
   - Why cosine similarity is the standard metric for text embeddings and how it handles text length differences.
4. **Choosing an Embedding Model**:
   - Evaluating open-source models (`all-MiniLM-L6-v2`, `BGE`, `Nomic`) vs. API providers (`gemini-embedding-001`, `text-embedding-3-small`) using the **MTEB Benchmark**.
5. **Semantic vs. Keyword Search**:
   - Conceptual matching (synonyms, intent) vs. Lexical matching (BM25, exact tokens, part numbers).
6. **Known Weaknesses (The Negation & Antonym Trap)**:
   - Why embedding models struggle with `"not"`, negative constraints, and antonym polarity.
7. **Hands-On Task**:
   - Embed **50 diverse sentences**, implement a **top-5 similarity search engine in pure NumPy**, and inspect failure modes.

---

## 🧠 Core Mathematical Concepts

### 1. What is an Embedding Vector?
Language models convert discrete words and sentences into a high-dimensional continuous geometric space. 
For example, in `gemini-embedding-001`, each sentence is represented as a vector of **3,072 floating-point coordinates**:
$$\vec{v} = [0.0142, -0.0531, 0.0892, \dots, -0.0019] \in \mathbb{R}^{3072}$$

Sentences with similar conceptual meanings point in nearly the same direction in this 3,072-dimensional space.

---

### 2. Cosine Similarity vs. Euclidean Distance

#### A. Cosine Similarity
Measures the **cosine of the angle ($\theta$)** between two vectors:
$$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = \frac{\sum_{i=1}^d u_i v_i}{\sqrt{\sum_{i=1}^d u_i^2} \sqrt{\sum_{i=1}^d v_i^2}}$$

* **Range**: $[-1.0, 1.0]$ (typically $[0.0, 1.0]$ for text embeddings).
* **Length Invariant**: Whether a sentence is 5 words or 50 words, if they discuss the same concept, their angle $\theta$ is small, yielding a cosine similarity near $1.0$.

#### B. Euclidean Distance ($L_2$ Norm)
Measures the **straight-line geometric distance** between two points:
$$\text{Euclidean Distance}(u, v) = \|u - v\|_2 = \sqrt{\sum_{i=1}^d (u_i - v_i)^2}$$

* **Range**: $[0, \infty)$.
* **Sensitivity**: Affected by vector length (document length) unless vectors are $L_2$-normalized.

> [!NOTE]
> When vectors are normalized to unit length ($\|u\|_2 = 1$), Euclidean distance and Cosine similarity are mathematically linked:
> $$\|u - v\|_2^2 = 2 - 2 \cdot \cos(u, v)$$
> Thus, **maximizing cosine similarity is mathematically identical to minimizing Euclidean distance**.

---

### 3. Semantic vs. Keyword Search

| Feature | Keyword Search (BM25 / Elastic) | Semantic Search (Vector Embeddings) |
| :--- | :--- | :--- |
| **Matching Logic** | Exact token/word overlap | Geometric conceptual proximity |
| **Synonym Handling** | ❌ Fails on `"automobile"` vs `"car"` | ✅ Understands they mean the same thing |
| **Misspellings** | ⚠️ Needs fuzzy edit-distance | ✅ Robust to minor typos |
| **Exact IDs & Codes** | ✅ Finds `"INV-9824"` instantly | ❌ May confuse with `"INV-9825"` |
| **Production Best Practice** | **Hybrid Search** (Combine BM25 + Vector with Reciprocal Rank Fusion) |

---

### 4. Known Weaknesses: Why Embeddings Fail on Negation

#### The Negation Trap
Consider these two sentences:
* Sentence A: *"I love this smartphone, the camera takes breathtaking photos."*
* Sentence B: *"I do NOT like this smartphone, the camera is terrible, blurry, and completely useless."*

In vector space, these two sentences score **$>0.80$ cosine similarity**!

**Why?**
Embedding models cluster text by **topic and semantic field** (smartphones, cameras, photos, consumer tech). The single negative word `"NOT"` represents only 1 token out of 15, so 90% of the vector points in the same direction. Embedding models measure *topical relatedness*, not *logical truth values*.

#### How Production RAG Systems Fix This:
1. **Cross-Encoder Rerankers (e.g. Cohere Rerank, BGE-Reranker)**:
   - A bi-encoder embeds query and document separately.
   - A cross-encoder takes `(query, document)` together and runs full cross-attention across all tokens, properly penalizing negations.
2. **Hybrid Search**:
   - BM25 captures exact tokens like `"never"`, `"not"`, and specific codes.

---

## 🚀 How to Run the Benchmark

```bash
cd day_03/session_1
python main.py
```

The script will:
1. Embed 50 diverse sentences in batches using `gemini-embedding-001`.
2. Compute cosine similarities and Euclidean distances in pure NumPy.
3. Test semantic search without keyword overlap.
## 📈 Empirical Benchmark Results

We executed the benchmark on `gemini-embedding-001` (3,072 dimensions) across our 50-sentence corpus:

```text
===============================================================================================
 DAY 3 - SESSION 1: EMBEDDINGS, VECTOR SIMILARITY & INSPECTION
===============================================================================================
Embedding Model  : gemini-embedding-001
Corpus Size      : 50 sentences
Embeddings Shape : (50, 3072) (Dimensions: 3072 per vector)
===============================================================================================

[QUERY 1 - SEMANTIC MATCH (No shared keywords)]: "healthy eating and nutritious green meals"
-----------------------------------------------------------------------------------------------
#20 | Cosine: 0.6253 | L2: 0.866 | Vegetarian Mediterranean diets emphasize fresh olive oil, crisp vegetables, and legumes.
#16 | Cosine: 0.5940 | L2: 0.901 | Consuming high amounts of processed refined sugar has been linked to chronic metabolic diseases.
#43 | Cosine: 0.5797 | L2: 0.917 | High-intensity interval training burns substantial calories in compact twenty-minute sessions.
#13 | Cosine: 0.5770 | L2: 0.920 | The restaurant served an exquisite, steaming hot bowl of spicy ramen soup.
#15 | Cosine: 0.5592 | L2: 0.939 | Artisan sourdough bread requires a healthy fermentation starter and high-hydration dough.

[QUERY 2 - COSINE vs. EUCLIDEAN COMPARISON]: "software engineering with deep neural networks"
-----------------------------------------------------------------------------------------------
#1  | Cosine: 0.6954 | L2: 0.780 | Artificial intelligence models are rapidly transforming software development workflows.
#8  | Cosine: 0.6032 | L2: 0.891 | Version control using Git is an essential prerequisite for collaborative engineering.
#3  | Cosine: 0.6027 | L2: 0.891 | The new GPU cluster accelerates transformer training by more than four hundred percent.
#2  | Cosine: 0.5976 | L2: 0.897 | Python is one of the most widely used languages for data science and machine learning.
#9  | Cosine: 0.5881 | L2: 0.908 | Open-source large language models are becoming increasingly competitive with closed proprietary APIs.

[QUERY 3 - THE NEGATION FAILURE INSPECTION]: "I do NOT want a phone with a terrible camera"
-----------------------------------------------------------------------------------------------
#6  | Cosine: 0.7907 | L2: 0.647 | I do NOT like this smartphone, the camera is terrible, blurry, and completely useless.
#5  | Cosine: 0.6850 | L2: 0.794 | I absolutely love this smartphone, the camera takes breathtaking photos in low light.
#14 | Cosine: 0.5825 | L2: 0.914 | The restaurant served a freezing cold, unappetizing, stale bowl of vegetable soup.
#26 | Cosine: 0.5531 | L2: 0.945 | The company avoided bankruptcy and recorded record-breaking quarterly profits.
#42 | Cosine: 0.5345 | L2: 0.965 | Prioritizing eight hours of quality sleep every night is vital for cognitive memory consolidation.

[QUERY 4 - ANTONYM & FINANCIAL POLARITY TRAP]: "The company suffered insolvency and went out of business"
-----------------------------------------------------------------------------------------------
#25 | Cosine: 0.7775 | L2: 0.667 | The company declared bankruptcy after severe financial losses and mounting debts.
#26 | Cosine: 0.6420 | L2: 0.846 | The company avoided bankruptcy and recorded record-breaking quarterly profits.
#45 | Cosine: 0.6020 | L2: 0.892 | The marathon runner suffered an acute hamstring tear and was unable to finish the race.
#14 | Cosine: 0.5961 | L2: 0.899 | The restaurant served a freezing cold, unappetizing, stale bowl of vegetable soup.
#10 | Cosine: 0.5871 | L2: 0.909 | The operating system crashed with a blue screen kernel panic after the driver update.
```

### 🔬 Deep Dive: Where It Gets It Wrong
1. **The Polarity / Antonym Trap**:
   - In Query 4 (*"company suffered insolvency and went out of business"*), Sentence #26 (*"The company **avoided bankruptcy** and recorded **record-breaking quarterly profits**"*) scored a high **0.6420 cosine similarity** and ranked #2!
   - Vector models cluster documents around the shared topic (*corporate solvency, bankruptcy, company performance*). They are mathematically blind to logical antonyms without a cross-encoder reranker.
2. **Negation Blindness**:
   - In Query 3, asking for a phone that does *not* have a bad camera still matches both positive and negative reviews because both live in the same "smartphone camera reviews" manifold.

