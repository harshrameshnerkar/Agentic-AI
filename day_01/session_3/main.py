"""
Day 01 - Session 03: Generation Parameters & Streaming
Explore how LLM parameters influence responses:
  1. Temperature: Controls creativity vs determinism.
  2. Max Tokens: Constrains output length.
  3. Streaming: Streams tokens in real-time as they are generated.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")

client = OpenAI(api_key=api_key, base_url=base_url)


def test_temperature():
    """Shows how temperature changes randomness (0.0 = deterministic, 1.0 = creative)."""
    print("\n--- 1. Testing Temperature (0.0 vs 1.0) ---")
    prompt = "Explain Agentic AI in two sentences."

    for temp in [0.0, 1.0]:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            max_tokens=80
        )
        print(f"\n[Temperature: {temp}]")
        print(response.choices[0].message.content.strip())


def test_streaming():
    """Shows how to stream tokens chunk-by-chunk for instant feedback."""
    print("\n\n--- 2. Testing Streaming ---")
    print("Streaming output: ", end="", flush=True)

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "List 3 advantages of AI agents in bullet points."}],
        max_tokens=100,
        stream=True
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


def test_max_tokens():
    """Shows how max_tokens caps response length."""
    print("\n--- 3. Testing Max Tokens (capped at 25 tokens) ---")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Write a short poem about coding."}],
        max_tokens=25
    )
    print(response.choices[0].message.content.strip())
    print(f"(Finish reason: {response.choices[0].finish_reason})")


def main():
    print(f"Running generation parameter experiments using model: {model}")
    test_temperature()
    test_streaming()
    test_max_tokens()
    print("\nDone!")


if __name__ == "__main__":
    main()