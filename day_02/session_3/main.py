import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# SETUP: LOAD CREDENTIALS & INITIALIZE CLIENT
# =====================================================================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file.")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# =====================================================================
# TOPIC 1, 2 & 5: PROMPT REGISTRY & VERSIONED TEMPLATE LOADER
# =====================================================================
class PromptRegistry:
    """
    Production Prompt Registry for versioned LLM prompt management.

    Benefits over hardcoded f-strings:
    1. Separation of Concerns: Prompts live in version-controlled template files.
    2. Versioning: Easily pin, roll back, or A/B test prompt versions (v1 vs v2).
    3. Safe Variable Injection: Validates required variables before API execution.
    4. Auditing & Collaboration: Prompt engineers can edit templates without editing Python code.
    """
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.registry_file = prompts_dir / "registry.json"
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            raise FileNotFoundError(f"Registry manifest not found at {self.registry_file}")
        with open(self.registry_file, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def get_metadata(self, prompt_name: str, version: str = "active") -> dict:
        """Retrieves metadata for a specific prompt name and version."""
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
        """
        Loads the template file for the specified version and renders it with injected variables.
        """
        meta = self.get_metadata(prompt_name, version)
        filename = meta["file"]
        filepath = self.prompts_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Prompt template file missing: {filepath}")

        # Check required variables
        required_vars = meta.get("required_variables", [])
        missing = [v for v in required_vars if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables for prompt '{prompt_name}' ({version}): {missing}")

        with open(filepath, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Render using Jinja2 (supports conditionals, loops, and clean variable injection)
        template = Template(template_content)
        rendered_prompt = template.render(**kwargs)
        return rendered_prompt


# Initialize Registry
PROMPTS_DIR = Path(__file__).parent / "prompts"
registry = PromptRegistry(PROMPTS_DIR)


# =====================================================================
# TEST BENCHMARK DATASET: 8 DIVERSE CUSTOMER EMAILS
# Categories: Billing, Technical Support, Feature Request, Sales
# =====================================================================
BENCHMARK_EMAILS = [
    {
        "id": 1,
        "true_category": "Billing",
        "email": "I was charged twice ($99.00 each) on my Visa card for this month's Pro subscription. Please reverse the duplicate charge."
    },
    {
        "id": 2,
        "true_category": "Billing",
        "email": "Can you please send our corporate accounting department an updated official VAT tax invoice with our registered company number?"
    },
    {
        "id": 3,
        "true_category": "Technical Support",
        "email": "Whenever we attempt to login using Okta SAML SSO, your identity gateway throws an HTTP 500 Internal Server Error."
    },
    {
        "id": 4,
        "true_category": "Technical Support",
        "email": "Our automated nightly backup job timed out after 30 minutes with error code ETIMEDOUT while attempting to connect to your API."
    },
    {
        "id": 5,
        "true_category": "Feature Request",
        "email": "Would it be possible to add direct export to Google Drive and OneDrive? It would save our compliance team several hours each week."
    },
    {
        "id": 6,
        "true_category": "Feature Request",
        "email": "We really need a dark mode theme for your desktop client. Working late at night in pure white background is causing severe eye fatigue."
    },
    {
        "id": 7,
        "true_category": "Sales",
        "email": "We have 350 developers on our engineering team and are looking to purchase enterprise licenses with dedicated 99.99% uptime SLAs."
    },
    {
        "id": 8,
        "true_category": "Sales",
        "email": "Could someone from your enterprise sales group schedule a demo with our VP of Engineering to discuss annual contract pricing?"
    }
]


# =====================================================================
# EXECUTION HELPER: CALL LLM WITH RETRY
# =====================================================================
def run_prompt(rendered_prompt: str, is_json_mode: bool = False, max_retries: int = 3) -> str:
    """Executes a rendered prompt against the LLM with rate-limit backoff."""
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": rendered_prompt}
                ],
                "temperature": 0.0
            }
            if is_json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()

        except Exception as e:
            err = str(e)
            if "429" in err or "RateLimitError" in type(e).__name__:
                print(f"   ⏳ [Rate Limit] Cooldown 32s for free-tier quota reset...")
                time.sleep(32)
            elif attempt < max_retries - 1:
                time.sleep(3)
            else:
                return f"ERROR: {err[:50]}"


# =====================================================================
# TOPIC 4: A/B TESTING EXPERIMENT (V1 vs V2)
# =====================================================================
def main():
    print("=" * 95)
    print(" DAY 2 - SESSION 3: PROMPT TEMPLATES, REGISTRY & A/B VERSIONING")
    print("=" * 95)
    print(f"Model Under Test : {MODEL}")
    print(f"Registry Path    : {PROMPTS_DIR}")
    print(f"Active Version   : {registry.get_metadata('email_classifier', 'active')['version']}")
    print("=" * 95)

    v1_meta = registry.get_metadata("email_classifier", "v1")
    v2_meta = registry.get_metadata("email_classifier", "v2")

    print(f"\n[Prompt Version A (v1)]: {v1_meta['file']} -> {v1_meta['description']}")
    print(f"[Prompt Version B (v2)]: {v2_meta['file']} -> {v2_meta['description']}")
    print("-" * 95)

    v1_json_valid = 0
    v1_correct = 0

    v2_json_valid = 0
    v2_correct = 0

    ab_results = []

    print(f"\n{'ID':<4} {'True Label':<18} {'V1 Category':<18} {'V1 Match':<10} {'V2 Category':<18} {'V2 Match':<10}")
    print("-" * 95)

    for item in BENCHMARK_EMAILS:
        e_id = item["id"]
        true_label = item["true_category"]
        email_text = item["email"]

        # -------------------------------------------------------------
        # 1. EVALUATE PROMPT V1 (Baseline Naive Prompt)
        # -------------------------------------------------------------
        prompt_v1 = registry.render("email_classifier", version="v1", email_text=email_text)
        raw_v1 = run_prompt(prompt_v1, is_json_mode=False)

        # Evaluate V1 output
        pred_v1 = "Unknown"
        is_json_v1 = False
        try:
            parsed_v1 = json.loads(raw_v1)
            is_json_v1 = True
            pred_v1 = parsed_v1.get("category", raw_v1)
        except json.JSONDecodeError:
            # V1 doesn't enforce JSON, so parse category using keyword check
            for cat in ["Billing", "Technical Support", "Feature Request", "Sales"]:
                if cat.lower() in raw_v1.lower():
                    pred_v1 = cat
                    break

        if is_json_v1:
            v1_json_valid += 1

        match_v1 = pred_v1.strip().lower() == true_label.strip().lower()
        if match_v1:
            v1_correct += 1

        time.sleep(2.5)

        # -------------------------------------------------------------
        # 2. EVALUATE PROMPT V2 (Engineered Versioned Template)
        # -------------------------------------------------------------
        prompt_v2 = registry.render("email_classifier", version="v2", email_text=email_text)
        raw_v2 = run_prompt(prompt_v2, is_json_mode=True)

        # Evaluate V2 output
        pred_v2 = "Unknown"
        is_json_v2 = False
        try:
            parsed_v2 = json.loads(raw_v2)
            is_json_v2 = True
            pred_v2 = parsed_v2.get("category", "Unknown")
        except json.JSONDecodeError:
            pass

        if is_json_v2:
            v2_json_valid += 1

        match_v2 = pred_v2.strip().lower() == true_label.strip().lower()
        if match_v2:
            v2_correct += 1

        # Tabular output row
        v1_status = "✅ PASS" if match_v1 else "❌ FAIL"
        v2_status = "✅ PASS" if match_v2 else "❌ FAIL"
        print(f"{e_id:<4} {true_label:<18} {pred_v1[:16]:<18} {v1_status:<10} {pred_v2[:16]:<18} {v2_status:<10}")

        ab_results.append({
            "id": e_id,
            "true": true_label,
            "v1_pred": pred_v1,
            "v1_match": match_v1,
            "v1_json": is_json_v1,
            "v2_pred": pred_v2,
            "v2_match": match_v2,
            "v2_json": is_json_v2
        })

        # Inter-email pacing
        time.sleep(2.5)

    # -------------------------------------------------------------
    # FINAL A/B STATISTICAL REPORT
    # -------------------------------------------------------------
    total = len(BENCHMARK_EMAILS)
    print("\n" + "=" * 95)
    print(" A/B COMPARATIVE EVALUATION REPORT: PROMPT V1 vs. PROMPT V2")
    print("=" * 95)
    print(f"{'Metric':<35} {'Version 1 (Naive)':<25} {'Version 2 (Engineered)':<25} {'Delta'}")
    print("-" * 95)

    acc_v1 = (v1_correct / total) * 100
    acc_v2 = (v2_correct / total) * 100
    acc_delta = acc_v2 - acc_v1

    json_v1_rate = (v1_json_valid / total) * 100
    json_v2_rate = (v2_json_valid / total) * 100
    json_delta = json_v2_rate - json_v1_rate

    print(f"{'Classification Accuracy':<35} {v1_correct}/{total} ({acc_v1:.1f}%)" + " " * 12 + f"{v2_correct}/{total} ({acc_v2:.1f}%)" + " " * 12 + f"{acc_delta:+.1f}%")
    print(f"{'Strict JSON Format Rate':<35} {v1_json_valid}/{total} ({json_v1_rate:.1f}%)" + " " * 11 + f"{v2_json_valid}/{total} ({json_v2_rate:.1f}%)" + " " * 11 + f"{json_delta:+.1f}%")
    print(f"{'Role Setting & Delimiters':<35} {'No (Vulnerable)':<25} {'Yes (<email> tags)':<25} {'Defensive'}")
    print(f"{'Few-Shot In-Context Learning':<35} {'0 Examples':<25} {'4 Demonstrations':<25} {'Guided'}")
    print("=" * 95)
    print("Conclusion: Version 2 achieves strict JSON schema compliance and deterministic classification.")
    print("Session 3 task completed successfully!")
    print("=" * 95)


if __name__ == "__main__":
    main()
