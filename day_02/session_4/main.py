"""
Day 02 - Session 04: Raw OpenAI API vs. LangChain LCEL Pipeline
================================================================
Compares two production paradigms for LLM application development:
  1. Raw API: Direct OpenAI SDK calls with zero framework overhead.
  2. LangChain LCEL: Composable declarative pipeline (prompt | model | parser).

Architectural Comparison:
  - Raw API: Maximum speed, lightweight dependencies, full transparency.
  - LangChain: Declarative chaining, built-in retry/streaming, schema binding.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Literal, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Setup Credentials & Environment
# ---------------------------------------------------------------------------
local_env = Path(__file__).resolve().parent / ".env"
root_env = Path(__file__).resolve().parents[2] / ".env"

if local_env.exists():
    load_dotenv(local_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not API_KEY:
    print("Error: Missing OPENAI_API_KEY in .env")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Pydantic Output Schema
# ---------------------------------------------------------------------------
class ClassificationOutput(BaseModel):
    category: Literal["Billing", "Technical Support", "Feature Request", "Sales"] = Field(
        description="Assigned customer support category"
    )
    reasoning: str = Field(
        description="One-sentence justification for the assigned category"
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

# ---------------------------------------------------------------------------
# Paradigm A: Raw OpenAI SDK Call
# ---------------------------------------------------------------------------
raw_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

RAW_SYSTEM_PROMPT = """You are a customer support triage classifier.
Classify incoming customer emails into EXACTLY ONE category:
- Billing
- Technical Support
- Feature Request
- Sales

Output ONLY a valid JSON object matching:
{"category": "<Category>", "reasoning": "<1-sentence rationale>"}"""

def classify_with_raw_api(email_text: str) -> Dict[str, Any]:
    """Classifies an email using the direct OpenAI client."""
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

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    validated = ClassificationOutput.model_validate(parsed)

    return {
        "result": validated.model_dump(),
        "latency_ms": elapsed_ms,
        "method": "Raw SDK"
    }

# ---------------------------------------------------------------------------
# Paradigm B: LangChain Expression Language (LCEL) Pipeline
# ---------------------------------------------------------------------------
lc_llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.0
)

lc_parser = JsonOutputParser(pydantic_object=ClassificationOutput)

lc_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert customer support triage classifier.\n"
        "Classify the customer email into exactly one category: Billing, Technical Support, Feature Request, or Sales.\n"
        "{format_instructions}"
    )),
    ("user", "<email>\n{email}\n</email>")
])

# Declarative composition: Prompt | Model | Parser
lc_chain = lc_prompt | lc_llm | lc_parser

def classify_with_langchain(email_text: str) -> Dict[str, Any]:
    """Classifies an email using the declarative LangChain LCEL pipeline."""
    start_time = time.perf_counter()

    raw_output = lc_chain.invoke({
        "email": email_text,
        "format_instructions": lc_parser.get_format_instructions()
    })

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    validated = ClassificationOutput.model_validate(raw_output)

    return {
        "result": validated.model_dump(),
        "latency_ms": elapsed_ms,
        "method": "LangChain LCEL"
    }

# ---------------------------------------------------------------------------
# Benchmark & Comparative Evaluation
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 90)
    print(" DAY 02 - SESSION 04: RAW OPENAI SDK vs. LANGCHAIN LCEL PIPELINE")
    print("=" * 90)
    print(f"Target Model       : {MODEL}")
    print(f"Evaluation Cases   : {len(TEST_EMAILS)}")
    print("=" * 90)
    print()

    raw_latencies = []
    lc_latencies = []

    print(f"{'#':<3} {'True Category':<19} {'Raw SDK Match':<18} {'LangChain Match':<18} {'Consistency'}")
    print("-" * 90)

    for item in TEST_EMAILS:
        e_id = item["id"]
        true_cat = item["true_category"]
        text = item["email"]

        # Run Raw SDK
        res_raw = classify_with_raw_api(text)
        cat_raw = res_raw["result"]["category"]
        raw_latencies.append(res_raw["latency_ms"])

        time.sleep(0.5)

        # Run LangChain
        res_lc = classify_with_langchain(text)
        cat_lc = res_lc["result"]["category"]
        lc_latencies.append(res_lc["latency_ms"])

        raw_match = "PASS" if cat_raw.lower() == true_cat.lower() else "FAIL"
        lc_match = "PASS" if cat_lc.lower() == true_cat.lower() else "FAIL"
        consistent = "MATCH" if cat_raw.lower() == cat_lc.lower() else "DIVERGED"

        print(f"{e_id:<3} {true_cat:<19} {cat_raw} ({raw_match})".ljust(44) + f"{cat_lc} ({lc_match})".ljust(25) + consistent)
        time.sleep(0.5)

    avg_raw = sum(raw_latencies) / len(raw_latencies)
    avg_lc = sum(lc_latencies) / len(lc_latencies)

    print("-" * 90)
    print("PERFORMANCE SUMMARY:")
    print(f"  Average Latency - Raw SDK   : {avg_raw:.1f} ms")
    print(f"  Average Latency - LangChain : {avg_lc:.1f} ms")
    print()
    print("DESIGN TAKEAWAYS:")
    print("  1. Raw SDK: Best for high-throughput, low-latency microservices with zero framework lock-in.")
    print("  2. LangChain LCEL: Best for complex RAG pipelines, multi-tool agents, and multi-step workflows.")
    print("=" * 90)
    print("Comparative evaluation completed successfully.\n")


if __name__ == "__main__":
    main()
