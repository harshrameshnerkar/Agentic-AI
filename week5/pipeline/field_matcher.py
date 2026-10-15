"""Field-Level Matching and Scoring Engine for Week 5 Document Extraction.

Implements the official matching rules defined in FIELD_SPECIFICATION.md:
- Exact alphanumeric match for invoice_id and vendor_tax_id
- Normalized ISO date equality for invoice_date and due_date
- RapidFuzz token set ratio (>= 85%) for vendor_name and customer_name
- Numeric absolute epsilon (<= 0.02) for subtotal, tax_amount, and total_amount
- Enum string equality for currency and payment_terms
- True Negative credit: Both null = Correct (1.0)
"""

from __future__ import annotations
import re
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

try:
    from rapidfuzz import fuzz
    def calculate_fuzzy_ratio(s1: str, s2: str) -> float:
        return float(fuzz.token_set_ratio(s1, s2))
except ImportError:
    import difflib
    def calculate_fuzzy_ratio(s1: str, s2: str) -> float:
        """Pure Python fallback for token set ratio matching without external dependencies."""
        t1 = set(s1.lower().split())
        t2 = set(s2.lower().split())
        intersection = t1.intersection(t2)
        if not intersection:
            return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100.0
        sorted_inter = " ".join(sorted(intersection))
        sorted1 = " ".join(sorted(t1))
        sorted2 = " ".join(sorted(t2))
        r1 = difflib.SequenceMatcher(None, sorted_inter, sorted1).ratio()
        r2 = difflib.SequenceMatcher(None, sorted_inter, sorted2).ratio()
        r3 = difflib.SequenceMatcher(None, sorted1, sorted2).ratio()
        return max(r1, r2, r3) * 100.0

FIELD_NAMES = [
    "invoice_id",
    "invoice_date",
    "due_date",
    "vendor_name",
    "vendor_tax_id",
    "customer_name",
    "currency",
    "subtotal",
    "tax_amount",
    "total_amount",
    "payment_terms",
]


class FieldMatcher:
    """Evaluates field-level extraction accuracy against hand-keyed ground truth."""

    @staticmethod
    def is_empty(val: Any) -> bool:
        if val is None:
            return True
        if isinstance(val, str) and val.strip().lower() in ("", "null", "none", "n/a", "unknown"):
            return True
        return False

    @classmethod
    def match_invoice_id(cls, pred: Any, truth: Any) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        p_clean = re.sub(r'^(?:invoice\s*(?:#|no\.?)?:?|#\s*)', '', str(pred), flags=re.IGNORECASE).strip()
        t_clean = re.sub(r'^(?:invoice\s*(?:#|no\.?)?:?|#\s*)', '', str(truth), flags=re.IGNORECASE).strip()
        return p_clean.lower() == t_clean.lower()

    @classmethod
    def match_date(cls, pred: Any, truth: Any) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        p_str = pred.isoformat() if isinstance(pred, date) else str(pred).strip()[:10]
        t_str = truth.isoformat() if isinstance(truth, date) else str(truth).strip()[:10]
        return p_str == t_str

    @classmethod
    def match_fuzzy_name(cls, pred: Any, truth: Any, threshold: float = 85.0) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        p_clean = re.sub(r'\b(?:inc|corp|llc|plc|group|ltd|and|&)\b', '', str(pred), flags=re.IGNORECASE)
        t_clean = re.sub(r'\b(?:inc|corp|llc|plc|group|ltd|and|&)\b', '', str(truth), flags=re.IGNORECASE)
        score = calculate_fuzzy_ratio(p_clean.strip(), t_clean.strip())
        return score >= threshold

    @classmethod
    def match_tax_id(cls, pred: Any, truth: Any) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        # Keep only alphanumeric characters
        p_alpha = re.sub(r'[^A-Za-z0-9]', '', str(pred)).upper()
        t_alpha = re.sub(r'[^A-Za-z0-9]', '', str(truth)).upper()
        return p_alpha == t_alpha

    @classmethod
    def match_amount(cls, pred: Any, truth: Any, epsilon: float = 0.02) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        try:
            p_val = float(pred)
            t_val = float(truth)
            return abs(p_val - t_val) <= epsilon
        except (ValueError, TypeError):
            return False

    @classmethod
    def match_enum(cls, pred: Any, truth: Any) -> bool:
        if cls.is_empty(pred) and cls.is_empty(truth):
            return True
        if cls.is_empty(pred) or cls.is_empty(truth):
            return False
        p_val = getattr(pred, "value", str(pred)).strip().upper()
        t_val = getattr(truth, "value", str(truth)).strip().upper()
        return p_val == t_val

    @classmethod
    def match_field(cls, field_name: str, pred_val: Any, truth_val: Any) -> bool:
        """Dispatches matching logic based on field type."""
        if field_name == "invoice_id":
            return cls.match_invoice_id(pred_val, truth_val)
        if field_name in ("invoice_date", "due_date"):
            return cls.match_date(pred_val, truth_val)
        if field_name in ("vendor_name", "customer_name"):
            return cls.match_fuzzy_name(pred_val, truth_val)
        if field_name == "vendor_tax_id":
            return cls.match_tax_id(pred_val, truth_val)
        if field_name in ("subtotal", "tax_amount", "total_amount"):
            return cls.match_amount(pred_val, truth_val)
        if field_name in ("currency", "payment_terms"):
            return cls.match_enum(pred_val, truth_val)
        return str(pred_val).strip() == str(truth_val).strip()

    @classmethod
    def evaluate_document(
        cls,
        predicted: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Evaluates all 11 fields for a single document against ground truth."""
        results = {}
        for field in FIELD_NAMES:
            p_val = predicted.get(field)
            t_val = ground_truth.get(field)
            results[field] = cls.match_field(field, p_val, t_val)
        return results
