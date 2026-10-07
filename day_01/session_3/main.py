import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

# Initialize client (supports both standard OpenAI or custom endpoints)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ------------------------------------------------------------
# SAME PROMPT FOR TEMPERATURE EXPERIMENT
# ------------------------------------------------------------

PROMPT = """
Explain Agentic AI in 5 sentences and give one real-world example.
""".strip()

SYSTEM = "You are a concise AI/ML instructor."


# ------------------------------------------------------------
# REQUIRED TASK:
# TEMPERATURE = 0, 0.7, 1.2
# ------------------------------------------------------------

def temperature_test():

    print("\n" + "=" * 60)
    print("TEMPERATURE EXPERIMENT")
    print("=" * 60)

    for temperature in [0, 0.7, 1.2]:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM
                },
                {
                    "role": "user",
                    "content": PROMPT
                }
            ],
            temperature=temperature,
            max_tokens=250  # Gives enough tokens for 5 sentences + example
        )

        content = response.choices[0].message.content or "(No text returned)"
        print(f"\nTEMPERATURE = {temperature}")
        print("-" * 60)
        print(content.strip())


# ------------------------------------------------------------
# OTHER PARAMETERS — QUICK DEMO (top_p, max_tokens)
# ------------------------------------------------------------

def parameter_demo():

    print("\n" + "=" * 60)
    print("OTHER GENERATION PARAMETERS (top_p & max_tokens)")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM
            },
            {
                "role": "user",
                "content": "Explain what an LLM is in 2 short bullet points."
            }
        ],
        temperature=0.7,
        top_p=0.9,       # Nucleus sampling
        max_tokens=150   # Limits generated output
    )

    content = response.choices[0].message.content or "(No text returned)"
    print("\nTOP_P (0.9) + MAX_TOKENS (150):")
    print(content.strip())


# ------------------------------------------------------------
# STREAMING
# ------------------------------------------------------------

def streaming_demo():

    print("\n" + "=" * 60)
    print("STREAMING DEMONSTRATION")
    print("=" * 60)

    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Explain tokens in an LLM in one sentence."
            }
        ],
        max_tokens=100,
        stream=True
    )

    print()
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(
                chunk.choices[0].delta.content,
                end="",
                flush=True
            )
    print("\n")


# ------------------------------------------------------------
# SEED / REPRODUCIBILITY
# ------------------------------------------------------------

def seed_demo():

    print("\n" + "=" * 60)
    print("SEED / REPRODUCIBILITY")
    print("=" * 60)

    try:
        for run in range(2):
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": "Give three facts about machine learning."
                    }
                ],
                temperature=0.7,
                max_tokens=150,
                seed=42  # Attempt same seed for both runs
            )

            content = response.choices[0].message.content or "(No text returned)"
            print(f"\nRUN {run + 1}:")
            print(content.strip())

    except Exception as e:
        print(f"\n[Note on Seeds]:")
        print(f"The 'seed' parameter is natively supported by OpenAI.")
        print(f"Current endpoint ({MODEL}) does not support the 'seed' field: {e}")


# ------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------

def main():

    print("\nDAY 1 — SESSION 3")
    print("GENERATION PARAMETERS")
    print(f"MODEL: {MODEL}")

    # 1. Required core task: Temperature 0, 0.7, 1.2
    temperature_test()

    # 2. Other parameter demonstrations
    parameter_demo()

    # 3. Streaming demonstration
    streaming_demo()

    # 4. Seed reproducibility check
    seed_demo()

    print("\n" + "=" * 60)
    print("SESSION 3 COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()