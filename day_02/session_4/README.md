# Day 2 - Session 4: LangChain / LlamaIndex Intro vs. Raw API

Welcome to **Session 4** of **Day 2: Advanced Prompting & Structured Output**.

In this session, we demystify higher-level AI frameworks (**LangChain** & **LlamaIndex**), dissect **LCEL (LangChain Expression Language)**, and compare an LCEL pipeline against direct, **Raw API calls**.

---

## 🎯 What You Will Learn

1. **What Frameworks Actually Give You**:
   - Abstract interfaces for model swapping (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenAI`).
   - Composable chains using LCEL (`prompt | llm | parser`).
   - Pre-built ecosystem integrations (document loaders, vector stores, memory buffers, web search tools).
   - Unified async, batching, streaming, and observability (LangSmith) hooks.
2. **LCEL Basics (LangChain Expression Language)**:
   - Understanding the Unix-style pipe operator (`|`) to stream data from `PromptTemplate` $\rightarrow$ `ChatModel` $\rightarrow$ `OutputParser`.
3. **When Raw API Calls are the Better Choice**:
   - Microservices requiring sub-second startup, zero dependency bloat, and total transparency without mysterious call stacks.
4. **Hands-On Task**:
   - Rebuild our customer support email classifier **once with the Raw API** and **once with LangChain LCEL**, and document a **3-line reflection on which was preferred and why**.

---

## 🧠 Framework Comparison: Raw API vs. LangChain

```text
Raw API Workflow:
  User Input ──> Python String Formatting ──> client.chat.completions.create() ──> json.loads() ──> Pydantic Validate

LangChain LCEL Workflow:
  User Input ──> ChatPromptTemplate | ChatModel | JsonOutputParser ──> Validated Dict/Model
```

### Direct Architectural Trade-Off

| Dimension | Raw Provider SDK (OpenAI) | LangChain LCEL |
| :--- | :--- | :--- |
| **Dependencies** | Minimal (`openai` only). | Heavier (`langchain`, `langchain-core`, `langchain-openai`). |
| **Composability** | Manual procedural code. | Declarative pipe syntax (`prompt \| llm \| parser`). |
| **Provider Portability** | Tied to provider's SDK. | Swap `ChatOpenAI` $\leftrightarrow$ `ChatAnthropic` in 1 line. |
| **Debugging** | Clear, standard Python stack traces. | Deeper abstraction layers; debugging internal middleware can be complex. |
| **Bleeding-Edge Features** | Available immediately on Day 1. | May lag behind vendor feature releases. |
| **Best For** | Focused, high-performance microservices. | Complex multi-step agentic pipelines, RAG, and tool orchestration. |

---

## 💻 Code Comparison

### 1. Raw API Implementation
```python
response = raw_client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": RAW_SYSTEM_PROMPT},
        {"role": "user", "content": f"<email>\n{email_text}\n</email>"}
    ],
    temperature=0.0,
    response_format={"type": "json_object"}
)
parsed_json = json.loads(response.choices[0].message.content)
result = ClassificationOutput.model_validate(parsed_json)
```

### 2. LangChain LCEL Pipeline Implementation
```python
# 1. Prompt with automatic format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a classifier. {format_instructions}"),
    ("user", "<email>\n{email}\n</email>")
])

# 2. Model
llm = ChatOpenAI(model=MODEL, temperature=0.0)

# 3. Output Parser
parser = JsonOutputParser(pydantic_object=ClassificationOutput)

# 4. Declarative Chain
chain = prompt | llm | parser

# 5. Invocation
result = chain.invoke({
    "email": email_text,
    "format_instructions": parser.get_format_instructions()
})
```

---

## 🚀 How to Run the Benchmark

```bash
cd day_02/session_4
python main.py
```

The script will:
1. Run identical customer queries through both the **Raw API** and **LangChain LCEL**.
2. Measure and report execution latency.
3. Verify categorization consistency.
4. Output the required 3-line reflection.

---

## 📝 The 3-Line Reflection (Preference & Why)

1. **For single-turn classification and simple endpoints, I prefer the RAW API** because it has zero abstraction overhead, faster startup times, and complete code transparency without mysterious library wrapper stacks.
2. **For multi-step agentic workflows, autonomous tool calling, and RAG, I prefer LANGCHAIN** because LCEL's pipe operator (`prompt | model | parser`) creates clean, declarative pipelines with unified batching, streaming, and observability out of the box.
3. **Final Verdict**: Use the Raw API for focused, lightweight production microservices; adopt LangChain/LlamaIndex when project complexity demands orchestration across vector databases, persistent memory, and autonomous agents.
