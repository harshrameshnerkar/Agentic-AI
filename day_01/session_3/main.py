"""
Day 01 - Session 03: Generation Parameters & Streaming
======================================================
Explore how core LLM hyperparameters influence text generation:
  1. Temperature: Controls randomness and creativity (0.0 = deterministic, 1.2 = creative).
  2. Top-P (Nucleus Sampling): Bounds token selection to cumulative probability threshold.
  3. Max Tokens: Constrains the maximum length of the generated response.
  4. Streaming: Delivers tokens incrementally for responsive user interfaces.
  5. Seed: Attempts reproducible generation across identical requests.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Ensure UTF-8 output on Windows terminals
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

PROMPT = "Explain Agentic AI in 3 concise sentences and provide one practical real-world example."
SYSTEM_PROMPT = "You are an expert AI engineer explaining concepts with precision and clarity."


def test_temperature_effects() -> None:
    """
    Demonstrate how temperature affects response determinism.
    - Temperature 0.0: Greedy sampling, consistent and analytical.
    - Temperature 0.7: Balanced creativity, good for general assistance.
    - Temperature 1.2: High entropy, diverse and creative phrasing.
    """
    print("\n" + "=" * 75)
    print(" EXPERIMENT 1: TEMPERATURE VARIATION (0.0 vs 0.7 vs 1.2)")
    print("=" * 75)

    temperatures = [0.0, 0.7, 1.2]

    for temp in temperatures:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": PROMPT}
                ],
                temperature=temp,
                max_tokens=220
            )
            content = response.choices[0].message.content or "(No text returned)"
            print(f"\n[Temperature: {temp}]")
            print("-" * 75)
            print(content.strip())
        except Exception as e:
            print(f"\n[Temperature: {temp}] Execution error: {e}")


def test_top_p_and_max_tokens() -> None:
    """
    Demonstrate nucleus sampling (top_p) and output truncation (max_tokens).
    """
    print("\n" + "=" * 75)
    print(" EXPERIMENT 2: TOP_P (0.85) AND MAX TOKENS (100)")
    print("=" * 75)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "List 3 key differences between a chain and an autonomous agent."}
            ],
            temperature=0.5,
            top_p=0.85,
            max_tokens=120
        )
        content = response.choices[0].message.content or "(No text returned)"
        tokens_used = response.usage.total_tokens if response.usage else 0
        print("-" * 75)
        print(content.strip())
        print("-" * 75)
        print(f"Tokens consumed: {tokens_used}")
    except Exception as e:
        print(f"Parameter test error: {e}")


def test_streaming_generation() -> None:
    """
    Demonstrate real-time token streaming using server-sent events.
    """
    print("\n" + "=" * 75)
    print(" EXPERIMENT 3: REAL-TIME TOKEN STREAMING")
    print("=" * 75)
    print("Streaming output: ", end="", flush=True)

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "Define 'context window' in two bullet points."}
            ],
            max_tokens=100,
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\nStreaming error: {e}")


def test_seed_reproducibility() -> None:
    """
    Demonstrate deterministic generation using a fixed random seed.
    Note: Some third-party endpoints may not natively support the seed attribute.
    """
    print("=" * 75)
    print(" EXPERIMENT 4: SEED REPRODUCIBILITY CHECK (seed=42)")
    print("=" * 75)

    try:
        for run_idx in (1, 2):
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": "Name three essential qualities of production code."}
                ],
                temperature=0.7,
                max_tokens=100,
                seed=42
            )
            content = response.choices[0].message.content or "(No text returned)"
            print(f"\nRun #{run_idx}:")
            print(content.strip())
    except Exception as e:
        print(f"Seed reproducibility note: Endpoint {MODEL} handled seed with notice: {e}")


def main() -> None:
    print("=" * 75)
    print(" DAY 01 - SESSION 03: LLM GENERATION PARAMETERS & STREAMING")
    print("=" * 75)
    print(f"Active Model: {MODEL}")

    test_temperature_effects()
    test_top_p_and_max_tokens()
    test_streaming_generation()
    test_seed_reproducibility()

    print("\n" + "=" * 75)
    print("Session 03 generation experiments completed successfully.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()