"""
Day 01 - Session 02: Token Counting & Cost Estimation
======================================================
Learn how Large Language Models break text into tokens and how API pricing
is calculated based on input and output token consumption.
"""

from typing import List, Dict
import tiktoken

# ---------------------------------------------------------------------------
# Pricing Configuration (Prices per 1 Million tokens in USD)
# ---------------------------------------------------------------------------
# Example pricing based on typical cost-efficient frontier models
INPUT_PRICE_PER_1M = 0.15   # $0.15 per 1,000,000 input tokens
OUTPUT_PRICE_PER_1M = 0.60  # $0.60 per 1,000,000 output tokens
ENCODING_NAME = "cl100k_base"  # Standard tokenizer for OpenAI / modern LLM architectures
ESTIMATED_OUTPUT_TOKENS = 200  # Typical expected response length for demonstration

# ---------------------------------------------------------------------------
# Educational Sample Prompts of Increasing Complexity
# ---------------------------------------------------------------------------
PROMPTS: List[Dict[str, str]] = [
    {
        "name": "Short Definition",
        "text": "Explain artificial intelligence in simple terms."
    },
    {
        "name": "Python Explanation",
        "text": "Explain Python functions with a simple code example for a complete beginner."
    },
    {
        "name": "LLM Mechanism",
        "text": (
            "Explain how a large language model generates the next token. "
            "Cover tokenization, context windows, probability distribution, and sampling temperature."
        )
    },
    {
        "name": "RAG Architecture",
        "text": (
            "Explain Retrieval-Augmented Generation (RAG) end-to-end: "
            "document ingestion, chunking, embedding generation, vector similarity search, "
            "context assembly, and final grounded answer generation."
        )
    },
    {
        "name": "Agentic AI Architecture",
        "text": (
            "Design an autonomous Agentic AI system that receives a user goal, "
            "decomposes the goal into sub-tasks, selects appropriate tools, observes outputs, "
            "maintains persistent memory, and handles runtime execution failures."
        )
    }
]


def count_tokens(text: str, encoding_name: str = ENCODING_NAME) -> int:
    """
    Encode text using the specified tokenizer and return the token count.
    
    Why token counting matters:
    1. LLM context windows have strict token limits (e.g., 8k, 32k, 128k).
    2. API billing is based directly on tokens, not words or characters.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)


def calculate_cost(input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """
    Calculate the estimated cost for an API call based on token usage.
    
    Formula:
        cost = (token_count / 1,000,000) * price_per_million
    """
    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_1M
    total_cost = input_cost + output_cost
    
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }


def main() -> None:
    print("=" * 80)
    print(" DAY 01 - SESSION 02: TOKEN COUNTING & COST ESTIMATION")
    print("=" * 80)
    print(f"Tokenizer Model      : {ENCODING_NAME}")
    print(f"Input Price / 1M     : ${INPUT_PRICE_PER_1M:.2f}")
    print(f"Output Price / 1M    : ${OUTPUT_PRICE_PER_1M:.2f}")
    print(f"Assumed Output Tokens: {ESTIMATED_OUTPUT_TOKENS}")
    print("=" * 80)
    print()

    total_input_tokens = 0
    total_estimated_cost = 0.0

    print(f"{'#':<3} {'Prompt Name':<25} {'Tokens':<8} {'Input Cost':<14} {'Total Cost':<14}")
    print("-" * 80)

    for index, item in enumerate(PROMPTS, start=1):
        name = item["name"]
        text = item["text"]

        # 1. Count input tokens
        input_tokens = count_tokens(text)
        
        # 2. Calculate projected cost
        cost_breakdown = calculate_cost(input_tokens, ESTIMATED_OUTPUT_TOKENS)

        total_input_tokens += input_tokens
        total_estimated_cost += cost_breakdown["total_cost"]

        print(
            f"{index:<3} {name:<25} {input_tokens:<8} "
            f"${cost_breakdown['input_cost']:<13.6f} ${cost_breakdown['total_cost']:<13.6f}"
        )

    print("-" * 80)
    print(f"Summary:")
    print(f"  Total Prompts Evaluated : {len(PROMPTS)}")
    print(f"  Total Input Tokens      : {total_input_tokens}")
    print(f"  Total Estimated Cost    : ${total_estimated_cost:.6f}")
    print("=" * 80)
    print("Token counting and estimation completed successfully.\n")


if __name__ == "__main__":
    main()