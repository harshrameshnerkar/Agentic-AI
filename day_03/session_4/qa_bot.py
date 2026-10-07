"""
qa_bot.py
=========
Enterprise Document Q&A Bot over 3 Business & Technical PDFs (Day 3 - Session 4)

Features:
- Citations: Cites exact document and page number for every answer
- Reranking: Uses Cross-Encoder to optimize candidate passage selection
- Grounding: Strict factual compliance rules preventing hallucinations
- Safe Refusal: Detects out-of-domain queries and gracefully refuses
- Dual Modes: Interactive CLI conversation or Automated Benchmark suite
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 terminal encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from pipeline import RAGPipeline, RAGQueryResult

SAMPLE_QUESTIONS = [
    {
        "category": "In-Domain (Cloud SLA)",
        "question": "What is the Monthly Uptime Percentage for Tier 1 services, and what penalty credit applies if uptime is 99.85%?",
    },
    {
        "category": "In-Domain (Cloud SLA)",
        "question": "What are the guaranteed RTO and RPO metrics for database disaster recovery, and when is DDoS excluded?",
    },
    {
        "category": "In-Domain (Travel Policy)",
        "question": "Under what specific conditions can an employee fly business class, and who must authorize it?",
    },
    {
        "category": "In-Domain (Travel Policy)",
        "question": "What is the daily meal per diem allowance, and what are the emergency travel insurance policy details and hotline?",
    },
    {
        "category": "In-Domain (DB Migration)",
        "question": "What logical decoding plugin and tool power the CDC pipeline, and what is the maximum replication lag threshold?",
    },
    {
        "category": "In-Domain (DB Migration)",
        "question": "When is the cutover window scheduled, what DNS TTL is required, and what three conditions trigger an automated rollback?",
    },
    {
        "category": "Out-of-Domain (Trick Query)",
        "question": "What is the recommended recipe and oven temperature for baking homemade sourdough bread?",
    },
    {
        "category": "Out-of-Domain (Trick Query)",
        "question": "Who won the FIFA Men's World Cup football tournament in 2022 and what was the final score?",
    },
]


def format_bot_response(res: RAGQueryResult) -> str:
    """Formats the bot's structured response with metadata and citations."""
    output = []
    output.append("-" * 75)
    output.append(f"QUESTION: {res.query}")
    output.append("-" * 75)

    if res.is_refusal:
        output.append("[SAFE REFUSAL ACTIVATED - NO RELEVANT RESULTS FOUND]")
        output.append(f"Reason: {res.refusal_reason or 'Low relevance score.'}")
        output.append("\nBOT ANSWER:")
        output.append(res.answer)
    else:
        output.append("RETRIEVAL & RERANKING TELEMETRY:")
        for r in res.reranked_candidates:
            output.append(
                f"  • Rank #{r.reranker_rank} (Bi-Encoder #{r.bi_encoder_rank}): "
                f"{r.source} (Page {r.page}) | Cross-Encoder Logit: {r.rerank_score:+.2f} (Prob: {r.relevance_prob*100:.1f}%)"
            )

        output.append("\nBOT ANSWER (GROUNDED WITH CITATIONS):")
        output.append(res.answer)

        output.append("\nVERIFIED CITATIONS:")
        if res.citations:
            for cit in res.citations:
                output.append(f"  [✓] {cit}")
        else:
            output.append("  (No direct in-line citations detected)")

        lat = res.latency
        output.append(
            f"\nPERFORMANCE: Total {lat.get('total_ms', 0)}ms "
            f"(Retrieval: {lat.get('retrieval_ms', 0)}ms | Rerank: {lat.get('rerank_ms', 0)}ms | LLM: {lat.get('llm_ms', 0)}ms)"
        )

    output.append("-" * 75)
    return "\n".join(output)


def run_benchmark(pipeline: RAGPipeline):
    """Runs automated Q&A benchmark across 8 test questions."""
    print("\n" + "=" * 80)
    print(" EXECUTING DOCUMENT Q&A BOT BENCHMARK (6 In-Domain + 2 Out-of-Domain)")
    print("=" * 80)

    for item in SAMPLE_QUESTIONS:
        cat = item["category"]
        q = item["question"]
        print(f"\n>>> [{cat}]")
        print(f"Query: {q}")
        res = pipeline.query(q)
        print(format_bot_response(res))
        time.sleep(3.5)  # Pace chat completions


def interactive_cli(pipeline: RAGPipeline):
    """Runs interactive command line Q&A interface."""
    print("\n" + "=" * 80)
    print(" ENTERPRISE DOCUMENT Q&A BOT (Interactive Mode)")
    print(" Ingested PDFs: Cloud SLA, Employee Travel Policy, DB Migration Guide")
    print(" Type your question and press Enter. Type 'exit' or 'quit' to leave.")
    print("=" * 80 + "\n")

    while True:
        try:
            user_input = input("\nYour Question > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Q&A Bot. Goodbye!")
                break

            print("\nProcessing (Retrieve -> Rerank -> Ground -> Synthesize)...")
            res = pipeline.query(user_input)
            print(format_bot_response(res))

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


if __name__ == "__main__":
    pipeline = RAGPipeline()
    docs_dir = Path(__file__).parent / "docs"
    pipeline.ingest_documents(docs_dir)

    # Check CLI arguments: if '--interactive' passed, run interactive mode; else run benchmark
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_cli(pipeline)
    else:
        run_benchmark(pipeline)
