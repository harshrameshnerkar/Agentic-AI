"""
Day 01 - Session 02: Token Counting & Cost Estimation
Learn how LLMs break text into tokens and estimate API costs based on token usage.
"""

import tiktoken

# Pricing per 1 Million tokens (example pricing)
INPUT_PRICE_PER_1M = 0.15   # $0.15 per 1M input tokens
OUTPUT_PRICE_PER_1M = 0.60  # $0.60 per 1M output tokens
ENCODING_NAME = "cl100k_base"
ESTIMATED_OUTPUT_TOKENS = 200

# Sample prompts to analyze
PROMPTS = [
    {"name": "Short Definition", "text": "Explain artificial intelligence in simple terms."},
    {"name": "Python Code", "text": "Explain Python functions with a simple code example for a complete beginner."},
    {"name": "LLM Explanation", "text": "Explain how a large language model generates the next token with sampling and temperature."},
    {"name": "RAG Concept", "text": "Explain Retrieval-Augmented Generation (RAG) end-to-end: chunking, embeddings, retrieval, and generation."},
    {"name": "Agentic AI", "text": "Design an autonomous Agentic AI system that plans tasks, calls tools, and remembers context."}
]

encoding = tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text: str) -> int:
    """Returns number of tokens in the given text."""
    return len(encoding.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculates total cost for input and expected output tokens."""
    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_1M
    return input_cost + output_cost


def main():
    print("=== Token Counting & Cost Estimation ===")
    print(f"Tokenizer: {ENCODING_NAME}")
    print(f"Pricing: ${INPUT_PRICE_PER_1M}/1M input, ${OUTPUT_PRICE_PER_1M}/1M output\n")

    total_tokens = 0
    total_cost = 0.0

    for i, prompt in enumerate(PROMPTS, 1):
        num_tokens = count_tokens(prompt["text"])
        cost = estimate_cost(num_tokens, ESTIMATED_OUTPUT_TOKENS)

        total_tokens += num_tokens
        total_cost += cost

        print(f"{i}. {prompt['name']}")
        print(f"   Tokens: {num_tokens}")
        print(f"   Estimated cost (prompt + {ESTIMATED_OUTPUT_TOKENS} output tokens): ${cost:.6f}\n")

    print("-" * 40)
    print(f"Total input tokens: {total_tokens}")
    print(f"Total estimated cost: ${total_cost:.6f}")


if __name__ == "__main__":
    main()