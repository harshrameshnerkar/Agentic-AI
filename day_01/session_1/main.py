"""
Day 01 - Session 01: First LLM API Call
========================================
Learn how to configure API credentials, initialize the OpenAI-compatible client,
and execute a structured chat completion request.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Ensure UTF-8 output formatting for terminal compatibility
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# 1. Environment & Credentials Setup
# ---------------------------------------------------------------------------
# Check local session folder first, then fall back to workspace root
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
    print("Error: OPENAI_API_KEY is missing. Please configure your .env file.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Client Initialization
# ---------------------------------------------------------------------------
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# ---------------------------------------------------------------------------
# 3. Chat Completion Execution
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print(" DAY 01 - SESSION 01: FIRST LLM API CALL")
    print("=" * 70)
    print(f"Target Model: {MODEL}")
    print("Sending prompt to model...\n")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a clear and concise AI educator."
                },
                {
                    "role": "user",
                    "content": "Explain what an LLM API is in one concise sentence."
                }
            ],
            temperature=0.2,
            max_tokens=100
        )

        reply = response.choices[0].message.content or "(Empty response)"
        total_tokens = response.usage.total_tokens if response.usage else 0

        print("Response received:")
        print("-" * 70)
        print(reply.strip())
        print("-" * 70)
        print(f"Total tokens consumed: {total_tokens}")
        print("API call completed successfully.\n")

    except Exception as e:
        print(f"API Execution Error: {e}")
        print("Ensure your API key and base URL are correctly configured in .env.")


if __name__ == "__main__":
    main()
