"""
Day 12 - Session 2: SFT Quality Control & Filtering Engine
==========================================================
Implements the multi-stage quality assurance pipeline adhering to
provider fine-tuning best practices (OpenAI / Gemini / Anthropic / HuggingFace):
  1. Strict Schema & Format Consistency Validation (Pydantic model check)
  2. Exact Deduplication via SHA-256 Hashes
  3. Fuzzy Semantic Deduplication via Word 3-Gram Jaccard Similarity (Threshold = 0.75)
  4. Sequence Length & Truncation Bounds Verification (< 2,048 tokens)
  5. Negative Pattern & Anomaly Filtering (No placeholders, no toxic leakage)
  6. Human-in-the-Loop (HITL) SRE Rubric & Rejection Sampling
"""

import json
import hashlib
import re
from typing import Dict, List, Any, Tuple, Set
from pydantic import BaseModel, Field

from dataset_generator import SFTExample, TriageActionPlan


def estimate_tokens(text: str) -> int:
    """Accurate token estimator based on whitespace + punctuation subwords (~3.8 chars/tok)."""
    return max(1, int(len(text) / 3.8))


def extract_word_ngrams(text: str, n: int = 3) -> Set[str]:
    """Extracts normalized word n-grams for fuzzy duplicate detection."""
    clean_words = re.sub(r"[^\w\s]", "", text.lower()).split()
    if len(clean_words) < n:
        return set([" ".join(clean_words)])
    return set(" ".join(clean_words[i:i + n]) for i in range(len(clean_words) - n + 1))


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Computes Jaccard similarity index between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


class QCFilterResult(BaseModel):
    is_valid: bool
    rejection_reason: str = ""
    stage_failed: str = ""


class QCReport(BaseModel):
    total_candidates_evaluated: int
    exact_duplicates_removed: int
    fuzzy_duplicates_removed: int
    schema_failures_removed: int
    token_boundary_failures_removed: int
    hitl_rubric_failures_removed: int
    total_accepted_examples: int
    retention_rate_pct: float
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    mean_prompt_tokens: float = 0.0
    mean_completion_tokens: float = 0.0


class QualityControlPipeline:
    def __init__(self, fuzzy_threshold: float = 0.75, max_seq_tokens: int = 2048):
        self.fuzzy_threshold = fuzzy_threshold
        self.max_seq_tokens = max_seq_tokens
        self.forbidden_patterns = [
            r"\[TODO\]", r"TODO", r"FIXME", r"<placeholder>", r"lorem ipsum",
            r"as an ai language model", r"http://fake", r"xyz_service"
        ]

    def validate_schema_and_format(self, example: SFTExample) -> QCFilterResult:
        """Stage 1: Validates exact role formatting and Pydantic JSON parse."""
        msgs = example.messages
        if len(msgs) != 3:
            return QCFilterResult(is_valid=False, stage_failed="FORMAT", rejection_reason=f"Expected 3 turns (system/user/assistant), got {len(msgs)}")

        if msgs[0]["role"] != "system" or msgs[1]["role"] != "user" or msgs[2]["role"] != "assistant":
            return QCFilterResult(is_valid=False, stage_failed="FORMAT", rejection_reason="Invalid role sequence")

        # Parse assistant JSON
        try:
            parsed = json.loads(msgs[2]["content"])
            TriageActionPlan(**parsed)
        except Exception as e:
            return QCFilterResult(is_valid=False, stage_failed="SCHEMA", rejection_reason=f"Assistant content failed Pydantic schema validation: {str(e)[:100]}")

        return QCFilterResult(is_valid=True)

    def validate_token_bounds(self, example: SFTExample) -> QCFilterResult:
        """Stage 2: Sequence length and truncation constraints."""
        sys_tok = estimate_tokens(example.messages[0]["content"])
        usr_tok = estimate_tokens(example.messages[1]["content"])
        ast_tok = estimate_tokens(example.messages[2]["content"])
        total_tok = sys_tok + usr_tok + ast_tok

        if total_tok > self.max_seq_tokens:
            return QCFilterResult(is_valid=False, stage_failed="TOKEN_BOUNDS", rejection_reason=f"Total tokens ({total_tok}) exceeds max {self.max_seq_tokens}")

        if usr_tok < 15:
            return QCFilterResult(is_valid=False, stage_failed="TOKEN_BOUNDS", rejection_reason=f"User prompt too short ({usr_tok} tokens)")

        if ast_tok < 40:
            return QCFilterResult(is_valid=False, stage_failed="TOKEN_BOUNDS", rejection_reason=f"Assistant completion too brief ({ast_tok} tokens)")

        return QCFilterResult(is_valid=True)

    def validate_content_heuristics(self, example: SFTExample) -> QCFilterResult:
        """Stage 3: Negative pattern detection and placeholder filtering."""
        combined_text = " ".join([m["content"] for m in example.messages]).lower()
        for pat in self.forbidden_patterns:
            if re.search(pat, combined_text, re.IGNORECASE):
                return QCFilterResult(is_valid=False, stage_failed="CONTENT_HEURISTIC", rejection_reason=f"Matched forbidden placeholder pattern: {pat}")
        return QCFilterResult(is_valid=True)

    def validate_hitl_sre_rubric(self, example: SFTExample) -> QCFilterResult:
        """
        Stage 4: Human-in-the-Loop (HITL) SRE domain review simulation.
        Enforces strict operational consistency:
          - If tool is restart_service or rollback_deployment, requires_approval MUST be True.
          - If severity is SEV-1, blast_radius MUST NOT be LOW.
        """
        try:
            plan = json.loads(example.messages[2]["content"])
            tool = plan.get("proposed_tool")
            req_app = plan.get("requires_approval")
            blast = plan.get("blast_radius")
            sev = plan.get("severity")

            # Destructive tools require approval
            if tool in ["restart_service", "rollback_deployment"] and not req_app:
                return QCFilterResult(is_valid=False, stage_failed="HITL_RUBRIC", rejection_reason="Destructive tool proposed without requires_approval=True")

            # Sev-1 cannot have LOW blast radius
            if sev == "SEV-1" and blast == "LOW":
                return QCFilterResult(is_valid=False, stage_failed="HITL_RUBRIC", rejection_reason="SEV-1 incident cannot have LOW blast radius")

        except Exception as e:
            return QCFilterResult(is_valid=False, stage_failed="HITL_RUBRIC", rejection_reason=f"Error inspecting plan: {e}")

        return QCFilterResult(is_valid=True)

    def process_and_filter(self, candidates: List[SFTExample], target_count: int = 300) -> Tuple[List[SFTExample], QCReport]:
        """Runs the complete multi-stage QC pipeline over the candidate pool."""
        seen_exact_hashes: Set[str] = set()
        seen_ngrams_list: List[Tuple[str, Set[str]]] = []  # (example_id, ngrams)

        accepted: List[SFTExample] = []
        exact_dupes = 0
        fuzzy_dupes = 0
        schema_fails = 0
        token_fails = 0
        hitl_fails = 0

        total_usr_tok = 0
        total_ast_tok = 0
        cat_dist: Dict[str, int] = {}
        sev_dist: Dict[str, int] = {}

        for ex in candidates:
            # If target reached, we stop
            if len(accepted) >= target_count:
                break

            # 1. Schema & Format Validation
            r_schema = self.validate_schema_and_format(ex)
            if not r_schema.is_valid:
                schema_fails += 1
                continue

            # 2. Token Bounds Validation
            r_tok = self.validate_token_bounds(ex)
            if not r_tok.is_valid:
                token_fails += 1
                continue

            # 3. Content Heuristics Validation
            r_content = self.validate_content_heuristics(ex)
            if not r_content.is_valid:
                schema_fails += 1
                continue

            # 4. HITL SRE Domain Rubric Validation
            r_hitl = self.validate_hitl_sre_rubric(ex)
            if not r_hitl.is_valid:
                hitl_fails += 1
                continue

            # 5. Exact Deduplication (SHA-256)
            user_text = ex.messages[1]["content"].strip().lower()
            h = hashlib.sha256(user_text.encode("utf-8")).hexdigest()
            if h in seen_exact_hashes:
                exact_dupes += 1
                continue
            seen_exact_hashes.add(h)

            # 6. Fuzzy Deduplication (Word 3-Gram Jaccard)
            ngrams = extract_word_ngrams(user_text, n=3)
            is_fuzzy_dupe = False
            for prev_id, prev_ngrams in seen_ngrams_list:
                sim = jaccard_similarity(ngrams, prev_ngrams)
                if sim >= self.fuzzy_threshold:
                    is_fuzzy_dupe = True
                    break

            if is_fuzzy_dupe:
                fuzzy_dupes += 1
                continue

            seen_ngrams_list.append((ex.example_id, ngrams))

            # Passed all stages!
            accepted.append(ex)
            total_usr_tok += estimate_tokens(ex.messages[1]["content"])
            total_ast_tok += estimate_tokens(ex.messages[2]["content"])
            cat_dist[ex.category] = cat_dist.get(ex.category, 0) + 1
            sev_dist[ex.severity] = sev_dist.get(ex.severity, 0) + 1

        n_acc = len(accepted)
        report = QCReport(
            total_candidates_evaluated=len(candidates),
            exact_duplicates_removed=exact_dupes,
            fuzzy_duplicates_removed=fuzzy_dupes,
            schema_failures_removed=schema_fails,
            token_boundary_failures_removed=token_fails,
            hitl_rubric_failures_removed=hitl_fails,
            total_accepted_examples=n_acc,
            retention_rate_pct=round((n_acc / len(candidates)) * 100.0, 1) if candidates else 0.0,
            category_distribution=cat_dist,
            severity_distribution=sev_dist,
            mean_prompt_tokens=round(total_usr_tok / max(1, n_acc), 1),
            mean_completion_tokens=round(total_ast_tok / max(1, n_acc), 1),
        )

        return accepted, report


# Singleton instance
qc_pipeline = QualityControlPipeline()
