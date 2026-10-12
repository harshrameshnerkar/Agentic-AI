"""
Day 02 - Session 03: Dynamic Prompt Templates & A/B Versioning
==============================================================
Demonstrates production prompt management using:
  1. File-based Jinja2 prompt templates
  2. A versioned PromptRegistry (manifest + template files)
  3. Dynamic variable injection with validation
  4. Empirical A/B testing: comparing v1 (naive prompt) vs v2 (engineered prompt)
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template

from dataset import BENCHMARK_EMAILS

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Setup Credentials & Client
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

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ---------------------------------------------------------------------------
# Production Prompt Registry
# ---------------------------------------------------------------------------
class PromptRegistry:
    """
    Manages versioned prompt templates stored in external files.
    Enables zero-code-change prompt updates, rollback, and A/B evaluations.
    """
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.registry_file = prompts_dir / "registry.json"
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.registry_file.exists():
            raise FileNotFoundError(f"Registry manifest not found at {self.registry_file}")
        with open(self.registry_file, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def get_metadata(self, prompt_name: str, version: str = "active") -> Dict[str, Any]:
        if prompt_name not in self.manifest:
            raise KeyError(f"Prompt '{prompt_name}' not found in registry.")

        config = self.manifest[prompt_name]
        actual_version = config["active_version"] if version == "active" else version

        if actual_version not in config["versions"]:
            raise KeyError(f"Version '{actual_version}' not registered for '{prompt_name}'.")

        meta = config["versions"][actual_version].copy()
        meta["version"] = actual_version
        return meta

    def render(self, prompt_name: str, version: str = "active", **kwargs) -> str:
        meta = self.get_metadata(prompt_name, version)
        filepath = self.prompts_dir / meta["file"]

        if not filepath.exists():
            raise FileNotFoundError(f"Prompt template missing: {filepath}")

        # Validate required variables
        required_vars = meta.get("required_variables", [])
        missing = [v for v in required_vars if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables for prompt '{prompt_name}': {missing}")

        with open(filepath, "r", encoding="utf-8") as f:
            template_content = f.read()

        return Template(template_content).render(**kwargs)


PROMPTS_DIR = Path(__file__).parent / "prompts"
registry = PromptRegistry(PROMPTS_DIR)


def execute_prompt(rendered_text: str, is_json_mode: bool = False) -> str:
    """Invokes LLM with rendered prompt."""
    try:
        kwargs: Dict[str, Any] = {
            "model": MODEL,
            "messages": [{"role": "user", "content": rendered_text}],
            "temperature": 0.0
        }
        if is_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        return f"ERROR: {str(e)[:50]}"


def run_ab_comparison(emails: List[Dict[str, Any]]) -> None:
    print("=" * 85)
    print(" DAY 02 - SESSION 03: PROMPT TEMPLATES, REGISTRY & A/B VERSIONING")
    print("=" * 85)
    print(f"Target Model       : {MODEL}")
    print(f"Evaluation Count   : {len(emails)}")
    print("Comparing          : Version 1 (Naive Prompt) vs Version 2 (Engineered Template)")
    print("=" * 85)
    print()

    v1_correct = 0
    v2_correct = 0

    print(f"{'#':<3} {'True Category':<18} {'V1 Prediction':<20} {'V2 Prediction':<20} {'Comparison'}")
    print("-" * 85)

    for item in emails:
        e_id = item["id"]
        true_cat = item["true_category"]
        text = item["email"]

        # 1. Version 1: Naive prompt
        prompt_v1 = registry.render("email_classifier", version="v1", email_text=text)
        res_v1 = execute_prompt(prompt_v1, is_json_mode=False)

        pred_v1 = "Unknown"
        for cat in ["Billing", "Technical Support", "Feature Request", "Sales"]:
            if cat.lower() in res_v1.lower():
                pred_v1 = cat
                break

        match_v1 = (pred_v1.lower() == true_cat.lower())
        if match_v1:
            v1_correct += 1

        time.sleep(0.5)

        # 2. Version 2: Engineered prompt
        prompt_v2 = registry.render("email_classifier", version="v2", email_text=text)
        res_v2 = execute_prompt(prompt_v2, is_json_mode=True)

        pred_v2 = "Unknown"
        try:
            parsed = json.loads(res_v2)
            pred_v2 = parsed.get("category", "Unknown")
        except Exception:
            pass

        match_v2 = (pred_v2.lower() == true_cat.lower())
        if match_v2:
            v2_correct += 1

        status_v1 = "PASS" if match_v1 else "FAIL"
        status_v2 = "PASS" if match_v2 else "FAIL"
        delta = "V2_BETTER" if (match_v2 and not match_v1) else ("TIED" if match_v1 == match_v2 else "V1_BETTER")

        print(f"{e_id:<3} {true_cat:<18} {pred_v1[:12]} ({status_v1})".ljust(43) + f"{pred_v2[:12]} ({status_v2})".ljust(22) + delta)
        time.sleep(0.5)

    print("-" * 85)
    print("A/B SUMMARY REPORT:")
    print(f"  Version 1 (Naive Prompt)      : {v1_correct}/{len(emails)} ({v1_correct / len(emails) * 100:.1f}%)")
    print(f"  Version 2 (Engineered Prompt) : {v2_correct}/{len(emails)} ({v2_correct / len(emails) * 100:.1f}%)")
    print("=" * 85)
    print("A/B prompt evaluation completed successfully.\n")


def main() -> None:
    if "--full" in sys.argv or "--all" in sys.argv:
        subset = BENCHMARK_EMAILS
    else:
        # 2 sample emails for fast demonstration
        subset = BENCHMARK_EMAILS[:2]
        print("[Note] Running 2-email demo. Pass '--full' to evaluate all 8 benchmark emails.\n")

    run_ab_comparison(subset)


if __name__ == "__main__":
    main()
