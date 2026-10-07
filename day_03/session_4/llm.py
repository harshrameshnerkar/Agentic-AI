"""
llm.py
======
STAGE 4 OF RAG: CONTEXT INJECTION & GROUNDED LLM SYNTHESIS (Day 3 - Session 4)

Responsibilities:
1. Context Injection: Formats reranked candidate excerpts with explicit source & page tags.
2. Grounding Rules: Formulates system prompts strictly enforcing fact fidelity and citations.
3. Cited Synthesis: Calls gemini-3.5-flash-lite and parses verified in-line page citations.
"""

import os
import re
import time
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv

from reranker import RerankedPassage

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")


class LLMResponse:
    """
    Structured container holding the synthesized answer, citations, and execution telemetry.
    """
    def __init__(
        self,
        query: str,
        answer: str,
        citations: List[str],
        latency_ms: float,
        is_refusal: bool = False,
    ):
        self.query = query
        self.answer = answer
        self.citations = citations
        self.latency_ms = latency_ms
        self.is_refusal = is_refusal

    def __repr__(self) -> str:
        return f"<LLMResponse citations={len(self.citations)} latency={self.latency_ms:.1f}ms>"


class LLMGenerator:
    """
    Injects reranked context into grounding prompt templates and synthesizes cited answers.
    """
    def __init__(self, model: str = CHAT_MODEL):
        self.model = model
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def assemble_injected_context(self, passages: List[RerankedPassage]) -> str:
        """
        Injects provenance metadata (source, page, chunk_id) into context excerpts.
        """
        context_blocks = []
        for p in passages:
            header = f"[DOCUMENT EXCERPT: {p.source} | Page: {p.page} | Chunk: {p.chunk_id}]"
            context_blocks.append(f"{header}\n{p.content}")

        return "\n\n" + ("=" * 60) + "\n\n".join(context_blocks)

    def generate(
        self,
        query: str,
        passages: List[RerankedPassage],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Executes Context Injection and Grounded LLM answer generation.
        """
        t0 = time.perf_counter()

        injected_context = self.assemble_injected_context(passages)

        system_prompt = """You are an enterprise compliance and technical Q&A assistant.
Your answers MUST be strictly grounded in the provided document excerpts.

MANDATORY GROUNDING RULES:
1. Strict Fidelity: Answer solely using the facts explicitly stated in the context. Never speculate or extrapolate.
2. In-Line Citations: For EVERY factual rule, metric, policy number, or threshold you state, you MUST cite the exact source and page in square brackets, for example:
   [Source: employee_travel_policy.pdf, Page: 2]
3. Missing Details: If the context answers only part of the question, state what is known and explicitly add:
   "The documentation does not provide details regarding [missing part]."
4. Structured Formatting: Use bullet points and bold headers for clarity."""

        user_prompt = f"""CONTEXT EXCERPTS:
{injected_context}

QUESTION:
{query}

ANSWER (with in-line source and page citations):"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                timeout=30.0,
            )
            answer_text = response.choices[0].message.content.strip()
        except Exception as e:
            answer_text = f"Error during answer generation: {e}"

        latency_ms = (time.perf_counter() - t0) * 1000

        # Extract verified page citations using regex
        raw_citations = list(set(re.findall(r"\[Source:\s*([^,\]]+),\s*Page:\s*(\d+)\]", answer_text)))
        citations = [f"{doc} (P{page})" for doc, page in raw_citations]

        return LLMResponse(
            query=query,
            answer=answer_text,
            citations=citations,
            latency_ms=round(latency_ms, 1),
            is_refusal=False,
        )


if __name__ == "__main__":
    generator = LLMGenerator()
    dummy_passages = [
        RerankedPassage(
            chunk_id="travel_p2_c0",
            content="Hotel lodging in Tier 1 cities like New York City is capped at $250.00 USD per night.",
            source="employee_travel_policy.pdf",
            page=2,
            bi_encoder_rank=1,
            reranker_rank=1,
            similarity=0.72,
            rerank_score=5.1,
            relevance_prob=0.99,
            metadata={},
        )
    ]
    resp = generator.generate("What is the hotel ceiling in NYC?", dummy_passages)
    print("Answer:\n", resp.answer)
    print("\nCitations:", resp.citations)
