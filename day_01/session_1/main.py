"""
Day 01 - Session 01: First LLM API Call
Learn how to configure API credentials, initialize the OpenAI client,
and execute a simple chat completion request.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key! Please set OPENAI_API_KEY or GEMINI_API_KEY in your .env file.")

# 2. Initialize the client
client = OpenAI(api_key=api_key, base_url=base_url)


def main():
    print(f"Calling model: {model}...")

    # 3. Request a chat completion
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful and concise AI tutor."},
            {"role": "user", "content": "Explain what an LLM API is in one concise sentence."}
        ],
        temperature=0.2,
        max_tokens=100
    )

    # 4. Display the response
    reply = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0

    print("\nResponse:")
    print("-" * 50)
    print(reply.strip())
    print("-" * 50)
    print(f"Total tokens used: {tokens_used}")


if __name__ == "__main__":
    main()
