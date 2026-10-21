"""Semantic and Mathematical Validator for Invoice Extraction.

Responsibilities:
- Checks types and constraints on candidate values extracted from documents.
- Evaluates domain business rules:
  1. Critical anchor presence (invoice_id, invoice_date, total_amount).
  2. Mathematical coherence (subtotal + tax_amount == total_amount).
  3. Chronological validity (invoice_date <= due_date).
  4. Non-negative values for monetary figures.
- Generates actionable diagnostic error messages for self-healing LLM retry loops.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from src.schemas import InvoiceExtraction


@dataclass
class ValidationIssue:
    field: str
    issue_type: str  # "SCHEMA_ERROR", "CONSTRAINT_ERROR", "ARITHMETIC_MISMATCH", "CHRONOLOGICAL_ERROR", "MISSING_ANCHOR"
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    extraction: Optional[InvoiceExtraction] = None
    issues: List[ValidationIssue] = field(default_factory=list)
    math_coherent: bool = True
    dates_coherent: bool = True
    anchors_present: bool = True

    def get_retry_prompt_feedback(self) -> str:
        """Formats issues into clear, concise feedback for the LLM retry prompt."""
        if not self.issues:
            return ""
        lines = ["The extracted invoice candidate data failed validation with the following issues:"]
        for issue in self.issues:
            lines.append(f"- [{issue.issue_type}] Field '{issue.field}': {issue.message}")
        lines.append("Please re-examine the document and fix ONLY the invalid fields while keeping valid fields intact.")
        return "\n".join(lines)


class InvoiceValidator:
    """Validates candidate invoice extractions against typing, constraints, and business rules."""

    MATH_EPSILON = Decimal("0.02")

    def validate_candidate_dict(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """Entrypoint for validating raw candidate dictionaries obtained by extractor."""
        # Step 1: Check types and schema constraints
        extraction, type_issues = self.check_types_and_constraints(raw_data)
        if extraction is None:
            return ValidationResult(
                is_valid=False,
                extraction=None,
                issues=type_issues,
                math_coherent=False,
                dates_coherent=False,
                anchors_present=False,
            )

        # Step 2: Check domain business rules
        rule_passed, rule_issues = self.check_business_rules(extraction)
        all_issues = type_issues + rule_issues

        has_blocking = any(i.issue_type in ("SCHEMA_ERROR", "CONSTRAINT_ERROR", "ARITHMETIC_MISMATCH") for i in all_issues)

        return ValidationResult(
            is_valid=not has_blocking,
            extraction=extraction,
            issues=all_issues,
            math_coherent=not any(i.issue_type == "ARITHMETIC_MISMATCH" for i in all_issues),
            dates_coherent=not any(i.issue_type == "CHRONOLOGICAL_ERROR" for i in all_issues),
            anchors_present=not any(i.issue_type == "MISSING_ANCHOR" for i in all_issues),
        )

    # Alias for backward compatibility
    validate_raw = validate_candidate_dict

    def check_types_and_constraints(
        self, raw_data: Dict[str, Any]
    ) -> Tuple[Optional[InvoiceExtraction], List[ValidationIssue]]:
        """Checks schema typing, parsing, and format constraints via Pydantic V2."""
        issues: List[ValidationIssue] = []
        try:
            extraction = InvoiceExtraction.model_validate(raw_data)
            return extraction, issues
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                issues.append(ValidationIssue(field=loc, issue_type="SCHEMA_ERROR", message=msg))
            return None, issues

    def check_business_rules(
        self, ext: InvoiceExtraction
    ) -> Tuple[bool, List[ValidationIssue]]:
        """Evaluates business rules: mathematical coherence, chronological order, anchors."""
        issues: List[ValidationIssue] = []

        # Rule 1: Critical Anchors
        if not ext.invoice_id:
            issues.append(ValidationIssue(
                field="invoice_id",
                issue_type="MISSING_ANCHOR",
                message="Invoice reference ID is missing or null.",
            ))
        if not ext.invoice_date:
            issues.append(ValidationIssue(
                field="invoice_date",
                issue_type="MISSING_ANCHOR",
                message="Invoice transaction date is missing or null.",
            ))
        if ext.total_amount is None:
            issues.append(ValidationIssue(
                field="total_amount",
                issue_type="MISSING_ANCHOR",
                message="Invoice total amount is missing or null.",
            ))

        # Rule 2: Mathematical Coherence
        if ext.subtotal is not None and ext.tax_amount is not None and ext.total_amount is not None:
            expected_total = (ext.subtotal + ext.tax_amount).quantize(Decimal("0.01"))
            actual_total = ext.total_amount.quantize(Decimal("0.01"))
            diff = abs(expected_total - actual_total)
            if diff > self.MATH_EPSILON:
                issues.append(ValidationIssue(
                    field="total_amount",
                    issue_type="ARITHMETIC_MISMATCH",
                    message=(
                        f"Arithmetic violation: subtotal ({ext.subtotal}) + tax_amount ({ext.tax_amount}) = "
                        f"{expected_total}, but total_amount is {actual_total} (diff: {diff})."
                    ),
                ))

        # Rule 3: Chronological Coherence
        if ext.invoice_date and ext.due_date:
            if ext.due_date < ext.invoice_date:
                issues.append(ValidationIssue(
                    field="due_date",
                    issue_type="CHRONOLOGICAL_ERROR",
                    message=f"due_date ({ext.due_date}) occurs before invoice_date ({ext.invoice_date}).",
                ))

        # Rule 4: Non-negative monetary amounts
        for field_name, val in (("subtotal", ext.subtotal), ("tax_amount", ext.tax_amount), ("total_amount", ext.total_amount)):
            if val is not None and val < Decimal("0.00"):
                issues.append(ValidationIssue(
                    field=field_name,
                    issue_type="CONSTRAINT_ERROR",
                    message=f"Monetary figure cannot be negative: {val}.",
                ))

        has_blocking = any(i.issue_type in ("CONSTRAINT_ERROR", "ARITHMETIC_MISMATCH") for i in issues)
        return not has_blocking, issues
