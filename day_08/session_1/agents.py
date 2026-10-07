"""
Specialized Agent implementations for Day 8 Session 1:
- SupervisorAgent (Orchestrator & Router)
- ResearcherAgent (Fact gathering & domain investigation)
- WriterAgent (Synthesis & publication-grade document generation)
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from state import MultiAgentState
from tools import RESEARCH_TOOLS_SCHEMA, query_knowledge_vault

# Load configuration
load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


def create_llm_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError("Missing API key in environment or .env file.")
    return OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


def call_llm_with_retry(client: OpenAI, **kwargs) -> Any:
    """Invokes LLM with exponential backoff for rate limits."""
    max_retries = 4
    delay = 3.0
    for attempt in range(1, max_retries + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as rle:
            if attempt == max_retries:
                raise rle
            time.sleep(delay * attempt)
        except Exception as e:
            if "rate" in str(e).lower() and attempt < max_retries:
                time.sleep(delay * attempt)
            else:
                raise e


class SupervisorAgent:
    """
    Central orchestrator agent. Inspects current state, determines
    the next workflow stage, and routes dynamically between workers.
    """

    SYSTEM_PROMPT = """You are the Lead Orchestration Supervisor managing an autonomous 2-agent team:
1. 'researcher': Investigates technical subjects, extracts facts, standards, and benchmarks.
2. 'writer': Synthesizes research notes into publication-ready executive briefings.

Your workflow responsibilities:
- Review the user's primary task and current state artifacts (research_notes, draft_report).
- Decide the NEXT best action:
  * If research_notes are absent or insufficient -> route to 'researcher'.
  * If research_notes exist but draft_report is missing -> route to 'writer'.
  * If draft_report exists and thoroughly satisfies the user prompt -> route to 'FINISH'.
  * If draft_report has critical omissions -> provide constructive critique and route back to 'writer' or 'researcher'.

CRITICAL INSTRUCTION: Output ONLY valid JSON with this exact schema:
{
  "next_agent": "researcher" | "writer" | "FINISH",
  "instructions": "Specific guidance for the chosen worker or final sign-off note",
  "rationale": "Clear reasoning explaining why this routing decision was selected",
  "quality_assessment": "Assessment of current artifacts against user task"
}
Do NOT include markdown backticks around the JSON. Output raw JSON only.
"""

    def __init__(self, client: Optional[OpenAI] = None, model: str = OPENAI_MODEL):
        self.client = client or create_llm_client()
        self.model = model

    def evaluate_and_route(self, state: MultiAgentState) -> Dict[str, Any]:
        """Examines state and produces structured routing decision."""
        state_summary = {
            "task": state["task"],
            "iteration": state["iteration"],
            "has_research_notes": bool(state.get("research_notes")),
            "research_notes_preview": (state["research_notes"][:300] + "...") if state.get("research_notes") else None,
            "has_draft_report": bool(state.get("draft_report")),
            "draft_report_preview": (state["draft_report"][:300] + "...") if state.get("draft_report") else None,
            "previous_feedback": state.get("review_feedback"),
        }

        user_content = (
            f"Current Multi-Agent State:\n{json.dumps(state_summary, indent=2)}\n\n"
            f"Decide the next routing step based on project progress."
        )

        response = call_llm_with_retry(
            self.client,
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0
        )

        raw_text = (response.choices[0].message.content or "").strip()
        # Clean any accidental markdown fencing
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            decision = json.loads(cleaned)
        except Exception:
            # Fallback heuristic if JSON parsing is malformed
            if not state.get("research_notes"):
                decision = {
                    "next_agent": "researcher",
                    "instructions": "Gather primary technical research and standards for the topic.",
                    "rationale": "Fallback: Research notes are not yet generated.",
                    "quality_assessment": "Pending research phase."
                }
            elif not state.get("draft_report"):
                decision = {
                    "next_agent": "writer",
                    "instructions": "Synthesize the gathered research notes into an executive briefing.",
                    "rationale": "Fallback: Research notes exist; proceed to writing.",
                    "quality_assessment": "Research notes ready."
                }
            else:
                decision = {
                    "next_agent": "FINISH",
                    "instructions": "Final draft report accepted.",
                    "rationale": "Fallback: All pipeline artifacts present.",
                    "quality_assessment": "Completed."
                }

        # Normalize next_agent
        target = decision.get("next_agent", "").strip().lower()
        if "research" in target:
            decision["next_agent"] = "researcher"
        elif "writ" in target:
            decision["next_agent"] = "writer"
        else:
            decision["next_agent"] = "FINISH"

        return decision


class ResearcherAgent:
    """
    Dedicated research worker. Uses domain knowledge tools to gather
    authoritative facts, standards, benchmark numbers, and technical details.
    """

    SYSTEM_PROMPT = """You are the Senior Technical Researcher.
Your job is to investigate technical subjects and compile structured, factual research notes.
Focus on:
1. Technical specifications, standards, and governing bodies (e.g. NIST, IEEE, IETF).
2. Key algorithmic or architectural components.
3. Industry adoption timelines, mandates, and deployment milestones.
4. Hard trade-offs, engineering bottlenecks, and operational challenges.

Present your research in structured Markdown with bullet points, exact metrics, and clear sections.
Be strictly factual. Do NOT write conversational filler.
"""

    def __init__(self, client: Optional[OpenAI] = None, model: str = OPENAI_MODEL):
        self.client = client or create_llm_client()
        self.model = model

    def research(self, task: str, supervisor_instructions: str) -> str:
        """Conducts research using domain lookup and synthesis."""
        # Query domain vault for relevant technical ground truth
        vault_data = query_knowledge_vault(task)

        context_prompt = (
            f"User Research Objective: {task}\n"
            f"Supervisor Directives: {supervisor_instructions}\n\n"
            f"Authoritative Domain Data Retrieved from Knowledge Vault:\n"
            f"{json.dumps(vault_data, indent=2)}\n\n"
            f"Synthesize these facts into comprehensive, structured research notes for our technical writer."
        )

        response = call_llm_with_retry(
            self.client,
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": context_prompt}
            ],
            temperature=0.1
        )

        return (response.choices[0].message.content or "").strip()


class WriterAgent:
    """
    Dedicated synthesis worker. Consumes structured research notes
    and crafts publication-ready executive briefings and technical reports.
    """

    SYSTEM_PROMPT = """You are the Principal Technical Writer and Executive Editor.
Your job is to transform raw technical research notes into an authoritative, publication-ready Executive Briefing.

Formatting & Style Requirements:
1. Title: Clear, professional briefing title.
2. Executive Summary: High-level overview of the strategic landscape in 2-3 sentences.
3. Technical Architecture & Standards: Detailed breakdown of algorithms, protocols, or frameworks.
4. Strategic Timelines & Industry Mandates: Key enterprise deadlines and adoption roadmaps.
5. Critical Engineering Challenges: Practical obstacles (e.g. packet fragmentation, hardware updates, threat models).
6. Actionable Recommendations: 3-4 prioritized next steps for engineering leaders.

Tone: Authoritative, analytical, concise, and structured.
Rely strictly on the facts provided in the research notes.
"""

    def __init__(self, client: Optional[OpenAI] = None, model: str = OPENAI_MODEL):
        self.client = client or create_llm_client()
        self.model = model

    def write(self, task: str, research_notes: str, supervisor_instructions: str) -> str:
        """Transforms research notes into an executive briefing."""
        user_prompt = (
            f"Primary Task: {task}\n"
            f"Supervisor Directives: {supervisor_instructions}\n\n"
            f"Authoritative Research Notes Provided by Research Team:\n"
            f"\"\"\"\n{research_notes}\n\"\"\"\n\n"
            f"Please write the complete executive briefing adhering to the formatting requirements."
        )

        response = call_llm_with_retry(
            self.client,
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        return (response.choices[0].message.content or "").strip()
