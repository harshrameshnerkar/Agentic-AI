"""Field-Level Accuracy Evaluation Engine for Document Extraction.

Responsibilities:
- Strictly separates human hand-keyed ground truth from model predictions.
- Loads ground truth from data/ground_truth/ground_truth.csv (the definitive source of truth).
- Loads candidate predictions from outputs/predictions.jsonl or passed-in prediction mapping.
- Compares predictions against ground truth using field-specific matching rules:
  1. Exact alphanumeric match for invoice_id and vendor_tax_id.
  2. Normalized ISO YYYY-MM-DD match for invoice_date and due_date.
  3. Fuzzy token set ratio (>= 85%) for vendor_name and customer_name.
  4. Decimal epsilon (<= 0.02) for subtotal, tax_amount, total_amount.
  5. Enum equality for currency and payment_terms.
- Generates outputs/accuracy_report.csv when evaluated.
"""

from __future__ import annotations
import csv
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from rapidfuzz import fuzz
    def calculate_fuzzy_ratio(s1: str, s2: str) -> float:
        return float(fuzz.token_set_ratio(s1, s2))
except ImportError:
    import difflib
    def calculate_fuzzy_ratio(s1: str, s2: str) -> float:
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
        for f in FIELD_NAMES:
            p_val = predicted.get(f)
            t_val = ground_truth.get(f)
            results[f] = cls.match_field(f, p_val, t_val)
        return results


@dataclass
class FieldAccuracyMetric:
    field_name: str
    total_evaluated: int
    correct_count: int
    accuracy_pct: float
    error_count: int
    match_rule: str


@dataclass
class EvaluationResults:
    total_documents: int
    field_metrics: Dict[str, FieldAccuracyMetric]
    overall_field_accuracy: float
    weakest_field_1: FieldAccuracyMetric
    weakest_field_2: FieldAccuracyMetric


class FieldEvaluator:
    """Calculates granular field-level extraction metrics comparing model predictions to ground truth."""

    RULE_DESCRIPTIONS = {
        "invoice_id": "Exact alphanumeric match (stripped prefixes)",
        "invoice_date": "Normalized ISO YYYY-MM-DD",
        "due_date": "Normalized ISO YYYY-MM-DD",
        "vendor_name": "Fuzzy token set ratio (>= 85%)",
        "vendor_tax_id": "Exact alphanumeric match",
        "customer_name": "Fuzzy token set ratio (>= 85%)",
        "currency": "Standardized ISO 4217 code",
        "subtotal": "Numeric difference <= 0.02 units",
        "tax_amount": "Numeric difference <= 0.02 units",
        "total_amount": "Numeric difference <= 0.02 units",
        "payment_terms": "Standardized Enum equality",
    }

    def __init__(
        self,
        ground_truth_path: Optional[Union[str, Path]] = None,
        predictions_path: Optional[Union[str, Path]] = None,
        output_csv_path: Optional[Union[str, Path]] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        # Ground truth is always loaded from data/ground_truth/ground_truth.csv
        self.gt_path = Path(ground_truth_path) if ground_truth_path else base_dir / "data" / "ground_truth" / "ground_truth.csv"
        self.predictions_path = Path(predictions_path) if predictions_path else base_dir / "outputs" / "predictions.jsonl"
        self.output_csv = Path(output_csv_path) if output_csv_path else base_dir / "outputs" / "accuracy_report.csv"
        self.matcher = FieldMatcher()

    def load_ground_truth(self) -> List[Dict[str, Any]]:
        """Loads human-keyed ground truth records (the correct answers)."""
        if not self.gt_path.exists():
            return []

        if self.gt_path.suffix.lower() == ".json":
            with open(self.gt_path, "r", encoding="utf-8") as f:
                return json.load(f)

        records = []
        with open(self.gt_path, "r", encoding="utf-8") as f:
            valid_lines = [line for line in f if line.strip()]
            reader = csv.DictReader(valid_lines)
            for row in reader:
                doc_id = row.get("document_id", "").strip()
                if not doc_id:
                    continue
                cleaned_row = {}
                for k, v in row.items():
                    if k in FIELD_NAMES:
                        cleaned_row[k] = None if v == "" or v is None else v
                    else:
                        cleaned_row[k] = v
                records.append(cleaned_row)
        return records

    def load_predictions(self, file_path: Optional[Union[str, Path]] = None) -> Dict[str, Dict[str, Any]]:
        """Loads model predictions from outputs/predictions.jsonl or fallback cache."""
        target_file = Path(file_path) if file_path else self.predictions_path
        pred_map: Dict[str, Dict[str, Any]] = {}

        if target_file.exists():
            if target_file.suffix.lower() == ".jsonl":
                with open(target_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            rec = json.loads(line)
                            doc_id = rec.get("document_id")
                            if doc_id:
                                pred_map[doc_id] = rec.get("extracted_data", {})
                return pred_map
            elif target_file.suffix.lower() == ".json":
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: v.get("extracted_data", {}) if isinstance(v, dict) and "extracted_data" in v else v for k, v in data.items()}

        # Fallback to cache if predictions.jsonl hasn't been generated yet
        base_dir = Path(__file__).resolve().parent.parent
        cache_path = base_dir / "data" / "extractions_cache.json"
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
                return {k: v.get("extracted_data", {}) for k, v in cache.items()}

        return pred_map

    def run_evaluation(
        self,
        predictions_map: Optional[Dict[str, Dict[str, Any]]] = None,
        predictions_file: Optional[Union[str, Path]] = None,
    ) -> EvaluationResults:
        """Evaluates model predictions against ground truth and dynamically writes accuracy_report.csv."""
        ground_truth_list = self.load_ground_truth()
        if not ground_truth_list:
            raise RuntimeError(f"Ground truth dataset could not be loaded from {self.gt_path}")

        # If predictions map not passed, load from predictions_file or outputs/predictions.jsonl
        if predictions_map is None:
            predictions_map = self.load_predictions(predictions_file)

        field_correct: Dict[str, int] = {f: 0 for f in FIELD_NAMES}
        total_docs = len(ground_truth_list)

        for gt in ground_truth_list:
            doc_id = gt.get("document_id") or Path(gt.get("filename", "")).stem
            # Model prediction for this document
            pred_data = predictions_map.get(doc_id, {})
            # Compare model prediction against human ground truth
            eval_map = self.matcher.evaluate_document(pred_data, gt)

            for field_name, is_match in eval_map.items():
                if is_match:
                    field_correct[field_name] += 1

        metrics: Dict[str, FieldAccuracyMetric] = {}
        for f in FIELD_NAMES:
            correct = field_correct[f]
            acc = round((correct / total_docs) * 100.0, 1)
            metrics[f] = FieldAccuracyMetric(
                field_name=f,
                total_evaluated=total_docs,
                correct_count=correct,
                accuracy_pct=acc,
                error_count=total_docs - correct,
                match_rule=self.RULE_DESCRIPTIONS.get(f, "Standard match"),
            )

        sorted_fields = sorted(metrics.values(), key=lambda x: x.accuracy_pct)
        weakest_1 = sorted_fields[0]
        weakest_2 = sorted_fields[1]

        total_correct = sum(m.correct_count for m in metrics.values())
        overall_acc = round((total_correct / (total_docs * len(FIELD_NAMES))) * 100.0, 1)

        results = EvaluationResults(
            total_documents=total_docs,
            field_metrics=metrics,
            overall_field_accuracy=overall_acc,
            weakest_field_1=weakest_1,
            weakest_field_2=weakest_2,
        )

        # Dynamically create outputs/accuracy_report.csv
        self.save_csv_report(results)
        return results

    def save_csv_report(self, res: EvaluationResults):
        """Generates outputs/accuracy_report.csv."""
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["field_name", "total_evaluated", "correct_count", "accuracy_pct", "error_count", "match_rule", "status"])
            for f in FIELD_NAMES:
                m = res.field_metrics[f]
                status = "WEAK" if m.field_name in (res.weakest_field_1.field_name, res.weakest_field_2.field_name) else "STRONG"
                writer.writerow([m.field_name, m.total_evaluated, m.correct_count, f"{m.accuracy_pct}%", m.error_count, m.match_rule, status])
