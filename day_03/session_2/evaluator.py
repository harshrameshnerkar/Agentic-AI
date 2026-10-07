"""
evaluator.py
============
RAG Retrieval & Answer Evaluation Benchmark (Day 3 - Session 2)

Systematically compares 300-token chunks vs. 800-token chunks across:
1. Retrieval Precision & Noise Ratio (context tokens consumed)
2. Source & Page citation fidelity
3. Ground Truth Fact Coverage (Did the retrieved context contain the answer?)
4. LLM Generation Quality (Accuracy, hallucination, omission)
"""

import os
import time
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from retriever import VectorRetriever, RetrievalResult
from embedder import Embedder

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")


BENCHMARK_QUESTIONS = [
    {
        "id": "Q1",
        "doc": "cloud_platform_sla.pdf",
        "question": "What is the guaranteed Monthly Uptime Percentage for Tier 1 services, and what percentage service credit is awarded if availability falls to 99.85%?",
        "ground_truth": "Tier 1 uptime is 99.995%. For availability below 99.90% but at or above 99.00% (which includes 99.85%), customers receive a 25% Service Credit.",
        "key_facts": ["99.995%", "25%", "Tier 1"],
    },
    {
        "id": "Q2",
        "doc": "cloud_platform_sla.pdf",
        "question": "What are the guaranteed RTO and RPO metrics for Tier 1 databases, and what DDoS attack threshold is excluded unless Enterprise Shield is active?",
        "ground_truth": "Recovery Time Objective (RTO) is 15 minutes. Recovery Point Objective (RPO) is 5 seconds. Volumetric DDoS attacks exceeding 500 Gbps are excluded unless enrolled in Enterprise Shield.",
        "key_facts": ["15 minutes", "5 seconds", "500 Gbps", "Enterprise Shield"],
    },
    {
        "id": "Q3",
        "doc": "employee_travel_policy.pdf",
        "question": "Under what specific conditions is an employee permitted to fly business class, whose approval is required, and is first class ever allowed?",
        "ground_truth": "Business class is restricted to non-stop transoceanic international flights exceeding 8 continuous hours (or multi-leg >12 hours), requiring prior written approval from the departmental Vice President (VP). First class is strictly prohibited under all circumstances.",
        "key_facts": ["exceeding eight (8) hours", "transoceanic", "Vice President", "First class is strictly prohibited"],
    },
    {
        "id": "Q4",
        "doc": "employee_travel_policy.pdf",
        "question": "What is the daily meal per diem ceiling and its breakdown, and what is the emergency medical travel insurance policy number and hotline?",
        "ground_truth": "Total per diem is $75.00/day ($15 breakfast, $25 lunch, $35 dinner). Emergency travel insurance policy number is GLOBAL-SEC-88421 with 24/7 hotline +1-800-555-0199.",
        "key_facts": ["$75.00", "$15", "$25", "$35", "GLOBAL-SEC-88421", "+1-800-555-0199"],
    },
    {
        "id": "Q5",
        "doc": "database_migration_guide.pdf",
        "question": "What tool and logical decoding plugin power the zero-downtime CDC pipeline, and what is the strict replication lag threshold required before cutover?",
        "ground_truth": "Powered by Debezium connectors running on Apache Kafka using the native 'pgoutput' logical decoding plugin with replication slot 'debezium_cdc_slot'. Replication lag must remain strictly under 250 milliseconds for at least 2 hours before cutover.",
        "key_facts": ["Debezium", "Apache Kafka", "pgoutput", "250 milliseconds"],
    },
    {
        "id": "Q6",
        "doc": "database_migration_guide.pdf",
        "question": "When is the production cutover window scheduled, what DNS TTL is required 48 hours prior, and what specific conditions trigger an immediate automated rollback?",
        "ground_truth": "Cutover window is Sunday between 02:00 UTC and 04:00 UTC. DNS TTL must be reduced to 60 seconds 48 hours prior. Automated rollback triggers if: (a) CDC queue fails to drain within 120 seconds; (b) HTTP 5xx error rate exceeds 0.05% for 3 consecutive minutes; or (c) query latency spikes by >300% on p99 or deadlocks exceed 50/min.",
        "key_facts": ["Sunday between 02:00 UTC and 04:00 UTC", "60 seconds", "120 seconds", "0.05%"],
    },
]


class BenchmarkEvaluator:
    """
    Orchestrates comparative RAG execution across 300-token vs 800-token index.
    """
    def __init__(self, embedder: Embedder, retriever_300: VectorRetriever, retriever_800: VectorRetriever):
        self.embedder = embedder
        self.retriever_300 = retriever_300
        self.retriever_800 = retriever_800
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def generate_answer(self, question: str, retrieved_results: List[RetrievalResult]) -> str:
        """
        Synthesizes an answer using the LLM strictly based on retrieved context chunks.
        """
        context_snippets = []
        for res in retrieved_results:
            header = f"[Source: {res.source} | Page: {res.page} | Chunk: {res.chunk_id}]"
            context_snippets.append(f"{header}\n{res.content}")

        joined_context = "\n\n---\n\n".join(context_snippets)

        prompt = f"""You are a precise enterprise compliance and technical assistant.
Answer the user's question STRICTLY and SOLELY based on the provided context excerpts below.
If the facts are not present in the context, explicitly state "Information not provided in context."
Always cite the source document and page number where you found each fact.

CONTEXT:
{joined_context}

QUESTION:
{question}

ANSWER:"""

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    timeout=30.0,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt < 2:
                    wait_time = 3.0 * (attempt + 1)
                    print(f"    [Retry Warning] chat generation failed ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return f"Error during generation: {e}"

    def check_key_facts(self, text: str, key_facts: List[str]) -> Dict[str, Any]:
        """
        Checks what fraction of key facts appear in the text (either retrieved context or answer).
        """
        found = [fact for fact in key_facts if fact.lower() in text.lower()]
        coverage = len(found) / len(key_facts) if key_facts else 0.0
        return {
            "found_count": len(found),
            "total_facts": len(key_facts),
            "coverage_pct": round(coverage * 100, 1),
            "missing_facts": [f for f in key_facts if f not in found],
        }

    def run_benchmark(self, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Executes comparison across all benchmark questions.
        """
        results_summary = []

        print(f"\n=======================================================")
        print(f"RUNNING RAG BENCHMARK: 300-TOKEN vs. 800-TOKEN CHUNKS")
        print(f"Top-K retrieved per question: {top_k}")
        print(f"=======================================================\n")

        for item in BENCHMARK_QUESTIONS:
            qid = item["id"]
            question = item["question"]
            key_facts = item["key_facts"]

            print(f"\n>>> Running {qid}: {question[:65]}...")

            # 1. Embed query
            q_vector = self.embedder.embed_query(question)
            time.sleep(1.0)  # pace queries

            # 2. Retrieve Top-K from 300-token index
            top_300 = self.retriever_300.search(q_vector, top_k=top_k)
            tokens_300 = sum(r.token_count for r in top_300)
            context_300 = "\n".join(r.content for r in top_300)
            facts_in_300 = self.check_key_facts(context_300, key_facts)

            # 3. Retrieve Top-K from 800-token index
            top_800 = self.retriever_800.search(q_vector, top_k=top_k)
            tokens_800 = sum(r.token_count for r in top_800)
            context_800 = "\n".join(r.content for r in top_800)
            facts_in_800 = self.check_key_facts(context_800, key_facts)

            # 4. Generate LLM answers for each
            print("  [Generating LLM answer with 300-token context]...")
            ans_300 = self.generate_answer(question, top_300)
            time.sleep(3.5)  # pace chat completions

            print("  [Generating LLM answer with 800-token context]...")
            ans_800 = self.generate_answer(question, top_800)
            time.sleep(3.5)  # pace chat completions

            eval_300 = self.check_key_facts(ans_300, key_facts)
            eval_800 = self.check_key_facts(ans_800, key_facts)

            record = {
                "id": qid,
                "question": question,
                "ground_truth": item["ground_truth"],
                "key_facts": key_facts,
                "top_k": top_k,
                "config_300": {
                    "chunks": [f"{r.source}:P{r.page} ({r.score:.3f})" for r in top_300],
                    "total_tokens": tokens_300,
                    "fact_coverage": facts_in_300["coverage_pct"],
                    "missing_facts": facts_in_300["missing_facts"],
                    "answer": ans_300,
                    "answer_fact_coverage": eval_300["coverage_pct"],
                },
                "config_800": {
                    "chunks": [f"{r.source}:P{r.page} ({r.score:.3f})" for r in top_800],
                    "total_tokens": tokens_800,
                    "fact_coverage": facts_in_800["coverage_pct"],
                    "missing_facts": facts_in_800["missing_facts"],
                    "answer": ans_800,
                    "answer_fact_coverage": eval_800["coverage_pct"],
                },
            }
            results_summary.append(record)

        return results_summary
