"""
Day 02 - Session 03: Dynamic Prompt Templates & A/B Versioning
Demonstrates prompt template management:
  1. File-based Jinja2 prompt templates
  2. PromptRegistry to load template versions
  3. A/B testing: Version 1 (Naive) vs Version 2 (Engineered with JSON)
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template
from dataset import BENCHMARK_EMAILS

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")

client = OpenAI(api_key=api_key, base_url=base_url)


class PromptRegistry:
    """Manages versioned Jinja2 prompt templates from a prompts/ folder."""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        with open(prompts_dir / "registry.json", "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def render(self, prompt_name: str, version: str = "active", **kwargs) -> str:
        config = self.manifest[prompt_name]
        ver = config["active_version"] if version == "active" else version
        template_file = self.prompts_dir / config["versions"][ver]["file"]

        with open(template_file, "r", encoding="utf-8") as f:
            return Template(f.read()).render(**kwargs)


registry = PromptRegistry(Path(__file__).parent / "prompts")


def call_llm(prompt_text: str, is_json: bool = False) -> str:
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.0
    }
    if is_json:
        kwargs["response_format"] = {"type": "json_object"}

    res = client.chat.completions.create(**kwargs)
    return (res.choices[0].message.content or "").strip()


def main():
    # Test on 2 sample emails by default, or --full for all 8
    emails = BENCHMARK_EMAILS if "--full" in sys.argv else BENCHMARK_EMAILS[:2]
    print(f"Running A/B evaluation on {len(emails)} email(s)...\n")

    for item in emails:
        text = item["email"]
        true_cat = item["true_category"]

        # Run V1 (Naive text prompt)
        p1 = registry.render("email_classifier", version="v1", email_text=text)
        res1 = call_llm(p1, is_json=False)

        # Run V2 (Structured prompt)
        p2 = registry.render("email_classifier", version="v2", email_text=text)
        res2 = call_llm(p2, is_json=True)
        try:
            pred2 = json.loads(res2).get("category", "Unknown")
        except Exception:
            pred2 = "Unknown"

        print(f"Email #{item['id']}: '{text[:45]}...'")
        print(f"  True:       {true_cat}")
        print(f"  V1 (Naive): {res1[:40]}...")
        print(f"  V2 (JSON):  {pred2}\n")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
