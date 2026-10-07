"""
Day 12 - Session 1: Architectural Decision Framework Engine
===========================================================
Implements the 8-Dimension Decision Framework evaluating whether an AI system
should utilize:
  - Tier 1: Prompt Engineering Only
  - Tier 2: In-Context RAG + Context Engineering (Current OpsSentinel AI)
  - Tier 3: Parameter-Efficient Fine-Tuning (PEFT / LoRA)
  - Tier 4: Self-Hosted Small Language Model (SLM) Distillation
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class EvaluationDimension(BaseModel):
    name: str
    weight: float
    description: str
    prompt_rag_score: float  # 0 to 10 scale (higher = better fit for Prompting/RAG)
    fine_tune_score: float   # 0 to 10 scale (higher = better fit for Fine-Tuning)
    assessment_notes: str


class FrameworkResult(BaseModel):
    project_name: str
    overall_recommendation: str
    executive_justification: str
    total_prompt_rag_score: float
    total_fine_tune_score: float
    recommendation_confidence: str
    dimension_breakdown: List[EvaluationDimension]
    risk_register: List[str]
    phase_gates: List[str]


class DecisionFrameworkEngine:
    def __init__(self):
        pass

    def evaluate_capstone(self) -> FrameworkResult:
        """Evaluates the Day 10-11 Capstone (OpsSentinel AI) against the 8 architectural dimensions."""
        dims = [
            EvaluationDimension(
                name="1. Knowledge Volatility",
                weight=1.5,
                description="Frequency with which domain facts, telemetry, runbooks, and microservices change.",
                prompt_rag_score=10.0,
                fine_tune_score=1.0,
                assessment_notes="SRE runbooks, active tickets, and infrastructure topologies change daily/minutely. RAG updates in 0 ms; fine-tuning requires slow retraining cycles.",
            ),
            EvaluationDimension(
                name="2. Grounding & Hallucination Risk",
                weight=1.5,
                description="Severity of catastrophic failure if the model invents plausible but incorrect remediation commands.",
                prompt_rag_score=10.0,
                fine_tune_score=2.0,
                assessment_notes="Mission-critical SRE operations require verbatim SOP citations and exact parameter matching. Fine-tuning produces probabilistic hallucination.",
            ),
            EvaluationDimension(
                name="3. Format & Schema Complexity",
                weight=1.0,
                description="Rarity or idiosyncrasy of the target output format (standard JSON vs proprietary AST).",
                prompt_rag_score=9.0,
                fine_tune_score=4.0,
                assessment_notes="OpsSentinel uses standard OpenAPI/JSON tool schemas and markdown summaries. Foundation models generate standard JSON flawlessly.",
            ),
            EvaluationDimension(
                name="4. Style & Persona Specificity",
                weight=0.8,
                description="Necessity of enforcing a proprietary brand voice or highly specialized linguistic style.",
                prompt_rag_score=8.5,
                fine_tune_score=7.0,
                assessment_notes="Concise professional SRE tone is fully achieved via a 126-token dense system prompt (proven in Day 11 Session 4).",
            ),
            EvaluationDimension(
                name="5. Token Budget Pressure",
                weight=1.0,
                description="Need to eliminate few-shot prompt overhead to save context tokens.",
                prompt_rag_score=9.0,
                fine_tune_score=6.0,
                assessment_notes="Context engineering cut prompt tokens by 62.4% (down to 408 tokens avg), rendering prompt bloat a non-issue.",
            ),
            EvaluationDimension(
                name="6. Latency Requirements",
                weight=1.0,
                description="Inference speed SLA (interactive human copilot vs sub-50ms robotic control).",
                prompt_rag_score=8.5,
                fine_tune_score=8.0,
                assessment_notes="OpsSentinel copilot targets p95 latency < 1.5 seconds. Current RAG pipeline executes in ~450 ms with prompt caching.",
            ),
            EvaluationDimension(
                name="7. Privacy & Air-Gap Constraints",
                weight=1.2,
                description="Regulatory or legal prohibition on sending prompts to external cloud APIs.",
                prompt_rag_score=7.5,
                fine_tune_score=5.0,
                assessment_notes="Enterprise infrastructure uses HIPAA/SOC-2 approved private cloud VPC endpoints. No absolute air-gap mandate currently exists.",
            ),
            EvaluationDimension(
                name="8. MLOps Budget & Team Maturity",
                weight=1.0,
                description="Availability of dedicated engineers to curate datasets, monitor drift, and maintain GPU clusters.",
                prompt_rag_score=9.5,
                fine_tune_score=2.0,
                assessment_notes="SRE team has strong platform engineering skills but zero appetite for ongoing GPU node management and dataset rot maintenance.",
            ),
        ]

        # Calculate weighted scores
        tot_rag = sum(d.prompt_rag_score * d.weight for d in dims)
        tot_ft = sum(d.fine_tune_score * d.weight for d in dims)
        max_possible = sum(10.0 * d.weight for d in dims)

        rag_norm = round((tot_rag / max_possible) * 100, 1)
        ft_norm = round((tot_ft / max_possible) * 100, 1)

        recommendation = "STAY ON IN-CONTEXT RAG + CONTEXT CACHING (REJECT FINE-TUNING)"
        justification = (
            f"The assessment yields a decisive {rag_norm}% alignment for In-Context RAG versus only {ft_norm}% "
            f"for Fine-Tuning. High knowledge volatility, zero tolerance for ungrounded hallucination, and standard JSON "
            f"tool calling make In-Context RAG the strictly superior architectural paradigm for OpsSentinel AI."
        )

        risks = [
            "RISK-1 (Parametric Hallucination): Fine-tuned models generate non-existent bash flags during remediation.",
            "RISK-2 (Knowledge Stagnation): Every SOP or microservice change requires retraining cycles taking 24-72 hours.",
            "RISK-3 (Financial Inefficiency): Dedicated GPU hosting costs 240x more than serverless RAG at 50k ops.",
            "RISK-4 (Catastrophic Forgetting): Training on SRE logs degrades reasoning on general logic and arithmetic.",
        ]

        gates = [
            "Gate 1: Re-evaluate if monthly volume exceeds 2,500,000 queries/month (Economic breakeven).",
            "Gate 2: Re-evaluate if regulatory mandates require 100% air-gapped on-premise execution.",
            "Gate 3: Re-evaluate if automated sub-80ms packet-level routing SLAs are mandated.",
            "Gate 4: Re-evaluate if frontier base models fail to adhere to proprietary internal schema formats.",
        ]

        return FrameworkResult(
            project_name="OpsSentinel AI (Day 10-11 Capstone)",
            overall_recommendation=recommendation,
            executive_justification=justification,
            total_prompt_rag_score=rag_norm,
            total_fine_tune_score=ft_norm,
            recommendation_confidence="VERY HIGH (DECISIVE)",
            dimension_breakdown=dims,
            risk_register=risks,
            phase_gates=gates,
        )


# Singleton instance
decision_framework = DecisionFrameworkEngine()
