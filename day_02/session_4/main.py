import os
import sys
import json
import time
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# SETUP: LOAD CREDENTIALS
# =====================================================================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file.")

# =====================================================================
# DATA SCHEMA & TEST DATASET
# =====================================================================
class ClassificationOutput(BaseModel):
    category: Literal["Billing", "Technical Support", "Feature Request", "Sales"] = Field(
        description="The assigned customer support category"
    )
    reasoning: str = Field(
        description="A concise 1-sentence rationale for the classification"
    )

TEST_EMAILS = [
    {
        "id": 1,
        "true_category": "Billing",
        "email": "I was charged twice on invoice #9021 for our team Pro subscription. Please refund the duplicate $49."
    },
    {
        "id": 2,
        "true_category": "Technical Support",
        "email": "Our developers are receiving 500 Internal Server Errors whenever attempting to call the webhook API."
    },
    {
        "id": 3,
        "true_category": "Feature Request",
        "email": "Can you please add native export to Notion and Google Docs? It would streamline our weekly reporting."
    },
    {
        "id": 4,
        "true_category": "Sales",
        "email": "We have 250 engineers and want to schedule a product demo to discuss enterprise licensing and custom SLAs."
    }
]

# =====================================================================
# IMPLEMENTATION A: RAW OPENAI API
# Direct SDK calls without framework abstractions.
# =====================================================================
from openai import OpenAI

raw_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

RAW_SYSTEM_PROMPT = """You are a customer support triage classifier.
Classify incoming emails into EXACTLY ONE category:
- Billing
- Technical Support
- Feature Request
- Sales

Return ONLY a valid JSON object matching:
{"category": "<Category>", "reasoning": "<1-sentence rationale>"}"""

def classify_with_raw_api(email_text: str) -> dict:
    """Classifies an email using raw OpenAI SDK calls."""
    start_time = time.perf_counter()

    response = raw_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": RAW_SYSTEM_PROMPT},
            {"role": "user", "content": f"<email>\n{email_text}\n</email>"}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    raw_content = response.choices[0].message.content.strip()
    parsed_json = json.loads(raw_content)

    # Validate with Pydantic
    validated = ClassificationOutput.model_validate(parsed_json)
    return {
        "result": validated.model_dump(),
        "latency_ms": elapsed_ms,
        "method": "Raw API"
    }


# =====================================================================
# IMPLEMENTATION B: LANGCHAIN LCEL PIPELINE
# Composable declarative pipeline using LangChain Expression Language (LCEL).
# =====================================================================
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 1. Initialize Chat Model
lc_llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.0
)

# 2. Output Parser grounded in Pydantic schema
lc_parser = JsonOutputParser(pydantic_object=ClassificationOutput)

# 3. Dynamic Prompt Template
lc_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert customer support triage classifier.\n"
        "Classify the customer email into exactly one category: Billing, Technical Support, Feature Request, or Sales.\n"
        "{format_instructions}"
    )),
    ("user", "<email>\n{email}\n</email>")
])

# 4. LCEL Composition: Prompt | Model | Parser
lc_chain = lc_prompt | lc_llm | lc_parser

def classify_with_langchain(email_text: str) -> dict:
    """Classifies an email using a LangChain LCEL pipeline."""
    start_time = time.perf_counter()

    # Invoke chain with input variables
    raw_output = lc_chain.invoke({
        "email": email_text,
        "format_instructions": lc_parser.get_format_instructions()
    })

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    validated = ClassificationOutput.model_validate(raw_output)

    return {
        "result": validated.model_dump(),
        "latency_ms": elapsed_ms,
        "method": "LangChain LCEL"
    }


# =====================================================================
# COMPARATIVE BENCHMARK EXECUTION
# =====================================================================
def main():
    print("=" * 95)
    print(" DAY 2 - SESSION 4: RAW API vs. LANGCHAIN LCEL PIPELINE")
    print("=" * 95)
    print(f"Model Under Test : {MODEL}")
    print(f"Total Emails     : {len(TEST_EMAILS)}")
    print("Comparing        : Raw OpenAI API vs. LangChain LCEL (prompt | llm | parser)")
    print("=" * 95)

    raw_times = []
    lc_times = []

    print(f"\n{'ID':<4} {'True Category':<19} {'Raw API Category':<20} {'LangChain Category':<22} {'Match':<8}")
    print("-" * 95)

    for item in TEST_EMAILS:
        e_id = item["id"]
        true_cat = item["true_category"]
        text = item["email"]

        # Run Raw API
        res_raw = classify_with_raw_api(text)
        cat_raw = res_raw["result"]["category"]
        raw_times.append(res_raw["latency_ms"])

        time.sleep(2.0)

        # Run LangChain LCEL
        res_lc = classify_with_langchain(text)
        cat_lc = res_lc["result"]["category"]
        lc_times.append(res_lc["latency_ms"])

        is_both_correct = (cat_raw == true_cat) and (cat_lc == true_cat)
        status = "✅ PASS" if is_both_correct else "❌ FAIL"

        print(f"{e_id:<4} {true_cat:<19} {cat_raw:<20} {cat_lc:<22} {status:<8}")

        time.sleep(2.0)

    avg_raw_ms = sum(raw_times) / len(raw_times)
    avg_lc_ms = sum(lc_times) / len(lc_times)

    print("-" * 95)
    print(f"Average Latency -> Raw API: {avg_raw_ms:.1f}ms | LangChain: {avg_lc_ms:.1f}ms")
    print("=" * 95)

    # -------------------------------------------------------------
    # REQUIRED DELIVERABLE: 3 LINES ON PREFERENCE & WHY
    # -------------------------------------------------------------
    print("\n" + "=" * 95)
    print(" REFLECTION: WHICH APPROACH I PREFERRED AND WHY (3 LINES)")
    print("=" * 95)
    print(
        "1. For single-turn classification and simple endpoints, I prefer the RAW API because it has zero\n"
        "   abstraction overhead, faster import times, and total transparency without mysterious library wrapper stacks."
    )
    print(
        "2. For multi-step agentic pipelines, tool calling, and RAG, I prefer LANGCHAIN because LCEL's pipe operator\n"
        "   (prompt | model | parser) creates elegant, declarative chains with unified batching, streaming, and tracing."
    )
    print(
        "3. Final Verdict: Use Raw API for focused, lightweight production microservices; adopt LangChain/LlamaIndex\n"
        "   only when project complexity demands orchestration across vector databases, memory, and autonomous tools."
    )
    print("=" * 95)
    print("Session 4 task completed successfully!")
    print("=" * 95)


if __name__ == "__main__":
    main()
