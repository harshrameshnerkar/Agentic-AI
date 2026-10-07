import tiktoken

# ------------------------------------------------------------
# 1. MODEL / PRICING CONFIGURATION
# ------------------------------------------------------------

# Tokenizer used by OpenAI GPT-style models.

# cl100k_base is commonly used for models such as GPT-4
# and GPT-3.5-era models.

# If you are using a provider/model with a different
# tokenizer, use that provider's recommended tokenizer.
ENCODING_NAME = "cl100k_base"

# ------------------------------------------------------------
# IMPORTANT:
# Replace these prices with the CURRENT pricing of the
# provider/model you are studying.
#
# Prices below are example values expressed as:
#
# INPUT_PRICE_PER_1M
# OUTPUT_PRICE_PER_1M
#
# Example:
# $0.15 per 1M input tokens
# $0.60 per 1M output tokens
# ------------------------------------------------------------

INPUT_PRICE_PER_1M = 0.15
OUTPUT_PRICE_PER_1M = 0.60

# ------------------------------------------------------------
# 2. CREATE TOKENIZER
# ------------------------------------------------------------

encoding = tiktoken.get_encoding(ENCODING_NAME)

# ------------------------------------------------------------
# 3. FIVE DIFFERENT PROMPTS
# ------------------------------------------------------------

prompts = [
    # Prompt 1 — Short
    {
        "name": "Prompt 1 - Short",
        "text": "Explain artificial intelligence."
    },

    # Prompt 2 — Medium
    {
        "name": "Prompt 2 - Python",
        "text": (
            "Explain Python functions with a simple example for a beginner."
        )
    },

    # Prompt 3 — LLM
    {
        "name": "Prompt 3 - LLM",
        "text": (
            "Explain how a large language model generates the next token. Include tokenisation, context window, probabilities, and sampling."
        )
    },

    # Prompt 4 — RAG
    {
        "name": "Prompt 4 - RAG",
        "text": (
            "Explain a Retrieval Augmented Generation system from document ingestion to chunking, embeddings, vector database retrieval, context construction, LLM generation, and final answer."
        )
    },

    # Prompt 5 — Agentic AI
    {
        "name": "Prompt 5 - Agentic AI",
        "text": (
            "Design an Agentic AI system that receives a user question, plans the required steps, selects tools, executes those tools, observes the results, updates its state, handles failures, and produces a final answer. Explain how memory, tool calling, planning, and validation work together."
        )
    }
]

# ------------------------------------------------------------
# 4. TOKEN COUNTING FUNCTION
# ------------------------------------------------------------
def count_tokens(text):
    """
    Convert text into tokens and return the number of tokens.
    """
    tokens = encoding.encode(text)
    return len(tokens)

# ------------------------------------------------------------
# 5. COST CALCULATION
# ------------------------------------------------------------
def calculate_input_cost(input_tokens):
    """
    Calculate estimated input-token cost.
    Formula:
        input_tokens / 1,000,000
        × input price per 1M tokens
    """
    return (input_tokens / 1_000_000) * INPUT_PRICE_PER_1M


def calculate_output_cost(output_tokens):
    """
    Calculate estimated output-token cost.
    """
    return (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_1M


def calculate_total_cost(input_tokens, output_tokens):
    """
    Calculate total estimated API cost.
    """
    input_cost = calculate_input_cost(input_tokens)
    output_cost = calculate_output_cost(output_tokens)
    return input_cost + output_cost

# ------------------------------------------------------------
# 6. ASSUMED OUTPUT TOKENS
# ------------------------------------------------------------

# We are only measuring the input prompt with tiktoken.
# An actual API call also generates output tokens.
# Therefore, we use an estimated output length here so students can understand how total cost is calculated.
# Change this value for different scenarios.

ESTIMATED_OUTPUT_TOKENS = 200

# ------------------------------------------------------------
# 7. MAIN PROGRAM
# ------------------------------------------------------------
def main():

    print()
    print("=" * 80)
    print("LLM TOKEN COUNTING & COST ESTIMATION")
    print("=" * 80)

    print()
    print(f"Tokenizer : {ENCODING_NAME}")
    print(f"Input price : ${INPUT_PRICE_PER_1M} / 1M tokens")
    print(f"Output  price : ${OUTPUT_PRICE_PER_1M} / 1M tokens")
    print(f"Estimated output tokens : {ESTIMATED_OUTPUT_TOKENS}")

    print()
    print("-" * 80)

    total_input_tokens = 0
    total_cost = 0

    # --------------------------------------------------------
    # Process all five prompts.
    # --------------------------------------------------------

    for prompt in prompts:
        name = prompt["name"]
        text = prompt["text"]

        # Count input tokens.
        input_tokens = count_tokens(text)

        # Calculate input cost.
        input_cost = calculate_input_cost(input_tokens)

        # Calculate estimated output cost.
        output_cost = calculate_output_cost(ESTIMATED_OUTPUT_TOKENS)

        # Calculate total call cost.
        total_call_cost = calculate_total_cost(input_tokens, ESTIMATED_OUTPUT_TOKENS)

        # Update totals.
        total_input_tokens += input_tokens
        total_cost += total_call_cost

        # ----------------------------------------------------
        # Print result.
        # ----------------------------------------------------
        print()
        print(f"NAME: {name}")
        print(f"Prompt:\n{text}")

        print()
        print(f"Input tokens       : {input_tokens}")
        print(f"Estimated output   : {ESTIMATED_OUTPUT_TOKENS}")
        print(f"Input cost         : ${input_cost:.8f}")
        print(f"Output cost       : ${output_cost:.8f}")
        print(f"Estimated total    : ${total_call_cost:.8f}")
        print("-" * 80)

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(f"Total input tokens : {total_input_tokens}")
    print(f"Total estimated cost : ${total_cost:.8f}")

    print()
    print("Token counting completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()