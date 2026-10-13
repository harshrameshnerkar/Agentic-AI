"""
Day 02 - Session 04: Raw OpenAI API vs. LangChain LCEL Pipeline
Compares two approaches to building LLM applications:
  1. Raw API: Direct OpenAI SDK calls.
  2. LangChain LCEL: Declarative pipeline (prompt | model | parser).
"""

import os
import json
import time
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")


class ClassificationOutput(BaseModel):
    category: Literal["Billing", "Technical Support", "Feature Request", "Sales"] = Field(
        description="Assigned category"
    )
    reasoning: str = Field(description="One-sentence reason")


TEST_EMAILS = [
    {"id": 1, "true_category": "Billing", "email": "I was charged twice on invoice #9021. Please refund $49."},
    {"id": 2, "true_category": "Technical Support", "email": "Our developers are receiving 500 errors from the API."},
    {"id": 3, "true_category": "Feature Request", "email": "Can you please add export to Notion and Google Docs?"},
    {"id": 4, "true_category": "Sales", "email": "We have 250 engineers and want to discuss enterprise pricing."}
]

# --- 1. Raw SDK Approach ---
raw_client = OpenAI(api_key=api_key, base_url=base_url)


def classify_raw(email: str) -> dict:
    t0 = time.perf_counter()
    res = raw_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Classify the email into Billing, Technical Support, Feature Request, or Sales. Output JSON with 'category' and 'reasoning'."},
            {"role": "user", "content": f"<email>{email}</email>"}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    data = json.loads(res.choices[0].message.content or "{}")
    return {"category": data.get("category", "Unknown"), "latency_ms": elapsed_ms}


# --- 2. LangChain LCEL Approach ---
lc_llm = ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.0)
lc_parser = JsonOutputParser(pydantic_object=ClassificationOutput)
lc_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify this email into Billing, Technical Support, Feature Request, or Sales.\n{format_instructions}"),
    ("user", "<email>{email}</email>")
])
lc_chain = lc_prompt | lc_llm | lc_parser


def classify_langchain(email: str) -> dict:
    t0 = time.perf_counter()
    res = lc_chain.invoke({
        "email": email,
        "format_instructions": lc_parser.get_format_instructions()
    })
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {"category": res.get("category", "Unknown"), "latency_ms": elapsed_ms}


def main():
    print(f"Comparing Raw OpenAI SDK vs LangChain LCEL using {model}...\n")

    for item in TEST_EMAILS:
        email = item["email"]
        true_cat = item["true_category"]

        res_raw = classify_raw(email)
        time.sleep(0.5)
        res_lc = classify_langchain(email)
        time.sleep(0.5)

        print(f"Email #{item['id']}: '{email[:40]}...'")
        print(f"  Target:    {true_cat}")
        print(f"  Raw SDK:   {res_raw['category']} ({res_raw['latency_ms']:.0f} ms)")
        print(f"  LangChain: {res_lc['category']} ({res_lc['latency_ms']:.0f} ms)\n")


if __name__ == "__main__":
    main()
