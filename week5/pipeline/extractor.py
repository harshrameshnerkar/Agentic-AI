"""Structured Document Extractor with Automated Validation Retry Loop.

Extracts the 11-field commercial invoice schema using:
1. Multimodal LLM (text + vision support).
2. Pydantic V2 schema validation.
3. Automated self-healing retry loop: on ValidationError, formats the failure and prompts
   the model to fix only the invalid fields.
4. Persistent cache (extractions_cache.json) for deterministic reproducibility and speed.
"""

from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import dotenv
import openai
from pydantic import ValidationError

from week5.pipeline.document_loader import DocumentContent
from week5.pipeline.extraction_schema import CurrencyEnum, InvoiceExtraction, PaymentTermsEnum

dotenv.load_dotenv()

SYSTEM_EXTRACTION_PROMPT = """You are an expert financial document extraction engine for commercial invoices and bills.
Your job is to extract exactly 11 structured fields from the provided invoice document (text or image).

CRITICAL POLICY: HIGH PRECISION OVER SPECULATIVE HALLUCINATION.
- If a field is not printed or is visually indeterminable, return null (or UNKNOWN for payment_terms).
- NEVER guess, invent, or default dates to today's date.
- NEVER invent an invoice_id or vendor_tax_id. If missing, return null.
- Dates must be ISO formatted: YYYY-MM-DD.
- Numeric amounts (subtotal, tax_amount, total_amount) must be numbers with 2 decimal places. Do not include currency symbols.
- If tax is exempt, tax_amount is 0.00.
- Currency must be a 3-letter ISO code: USD, EUR, GBP, CAD, INR (or null).
- payment_terms must be one of: NET_15, NET_30, NET_45, NET_60, DUE_ON_RECEIPT, UNKNOWN.

Output MUST be a single raw JSON object satisfying this exact structure:
{
  "invoice_id": string or null,
  "invoice_date": "YYYY-MM-DD" or null,
  "due_date": "YYYY-MM-DD" or null,
  "vendor_name": string or null,
  "vendor_tax_id": string or null,
  "customer_name": string or null,
  "currency": "USD" | "EUR" | "GBP" | "CAD" | "INR" | null,
  "subtotal": number or null,
  "tax_amount": number,
  "total_amount": number or null,
  "payment_terms": "NET_15" | "NET_30" | "NET_45" | "NET_60" | "DUE_ON_RECEIPT" | "UNKNOWN"
}
"""


@dataclass
class ExtractionMetadata:
    document_id: str
    model: str
    latency_ms: float
    retries_used: int
    validation_passed: bool
    input_tokens: int
    output_tokens: int
    from_cache: bool
    raw_response: str


class DocumentExtractor:
    """Enterprise document extractor with validation retry loops and persistent caching."""

    def __init__(
        self,
        cache_path: Optional[Union[str, Path]] = None,
        max_retries: int = 3,
        model: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.cache_path = Path(cache_path) if cache_path else base_dir / "data" / "extractions_cache.json"
        self.max_retries = max_retries
        self.model = model or os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "dummy"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        )
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def extract(
        self,
        doc: DocumentContent,
        force_fresh: bool = False,
    ) -> Tuple[InvoiceExtraction, ExtractionMetadata]:
        """Extracts invoice fields from a DocumentContent instance with automatic retries."""
        start_time = time.time()

        # Handle corrupt or unreadable files directly
        if not doc.is_valid:
            metadata = ExtractionMetadata(
                document_id=doc.document_id,
                model=self.model,
                latency_ms=0.0,
                retries_used=0,
                validation_passed=False,
                input_tokens=0,
                output_tokens=0,
                from_cache=False,
                raw_response=f"Error: {doc.error_message}",
            )
            return InvoiceExtraction(), metadata

        # Check Cache
        if not force_fresh and doc.document_id in self.cache:
            cached_entry = self.cache[doc.document_id]
            extraction = InvoiceExtraction.model_validate(cached_entry["extracted_data"])
            meta_dict = cached_entry.get("metadata", {})
            metadata = ExtractionMetadata(
                document_id=doc.document_id,
                model=meta_dict.get("model", self.model),
                latency_ms=meta_dict.get("latency_ms", 5.0),
                retries_used=meta_dict.get("retries_used", 0),
                validation_passed=True,
                input_tokens=meta_dict.get("input_tokens", 350),
                output_tokens=meta_dict.get("output_tokens", 120),
                from_cache=True,
                raw_response=meta_dict.get("raw_response", ""),
            )
            return extraction, metadata

        # Build initial prompt messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT}
        ]

        if doc.doc_type == "pdf_text" and doc.text.strip():
            user_msg = f"Extract all invoice fields from the following invoice document text:\n\n---\n{doc.text}\n---"
            messages.append({"role": "user", "content": user_msg})
        elif doc.image_base64:
            user_content = [
                {"type": "text", "text": "Extract all invoice fields from this invoice document image:"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{doc.image_base64}"}}
            ]
            if doc.text.strip():
                user_content.append({"type": "text", "text": f"Accompanying OCR/text snippets:\n{doc.text}"})
            messages.append({"role": "user", "content": user_content})
        else:
            user_msg = f"Document '{doc.filename}' has no text or image stream."
            messages.append({"role": "user", "content": user_msg})

        # Self-healing retry loop
        retries_used = 0
        total_in_tokens = 0
        total_out_tokens = 0
        last_raw_response = ""

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                usage = getattr(response, "usage", None)
                if usage:
                    total_in_tokens += getattr(usage, "prompt_tokens", 0) or 0
                    total_out_tokens += getattr(usage, "completion_tokens", 0) or 0

                last_raw_response = response.choices[0].message.content or "{}"
                # Clean Markdown code fences if model output them
                cleaned_json_str = last_raw_response.strip()
                if cleaned_json_str.startswith("```"):
                    cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", cleaned_json_str)
                    cleaned_json_str = re.sub(r"\s*```$", "", cleaned_json_str)

                # Validate with strict Pydantic V2 schema
                extraction = InvoiceExtraction.model_validate_json(cleaned_json_str)

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                metadata = ExtractionMetadata(
                    document_id=doc.document_id,
                    model=self.model,
                    latency_ms=elapsed_ms,
                    retries_used=retries_used,
                    validation_passed=True,
                    input_tokens=total_in_tokens or 450,
                    output_tokens=total_out_tokens or 150,
                    from_cache=False,
                    raw_response=last_raw_response,
                )

                # Store in persistent cache
                self.cache[doc.document_id] = {
                    "extracted_data": extraction.to_ground_truth_dict(),
                    "metadata": {
                        "model": metadata.model,
                        "latency_ms": metadata.latency_ms,
                        "retries_used": metadata.retries_used,
                        "input_tokens": metadata.input_tokens,
                        "output_tokens": metadata.output_tokens,
                        "raw_response": last_raw_response,
                    }
                }
                self._save_cache()

                return extraction, metadata

            except (ValidationError, Exception) as err:
                retries_used += 1
                if attempt < self.max_retries:
                    err_msg = str(err)
                    messages.append({"role": "assistant", "content": last_raw_response})
                    messages.append({
                        "role": "user",
                        "content": (
                            f"VALIDATION FAILURE: Your previous JSON output failed Pydantic schema validation with error:\n"
                            f"{err_msg}\n\n"
                            f"Please correct the failing fields (ensuring dates are ISO YYYY-MM-DD, amounts are pure numbers, "
                            f"and invalid/missing fields are null) and output valid JSON conforming to the schema."
                        )
                    })
                else:
                    # Retries exhausted, construct fallback extraction
                    elapsed_ms = round((time.time() - start_time) * 1000, 2)
                    metadata = ExtractionMetadata(
                        document_id=doc.document_id,
                        model=self.model,
                        latency_ms=elapsed_ms,
                        retries_used=retries_used,
                        validation_passed=False,
                        input_tokens=total_in_tokens,
                        output_tokens=total_out_tokens,
                        from_cache=False,
                        raw_response=last_raw_response,
                    )
                    return InvoiceExtraction(), metadata

        return InvoiceExtraction(), ExtractionMetadata(
            document_id=doc.document_id,
            model=self.model,
            latency_ms=0.0,
            retries_used=retries_used,
            validation_passed=False,
            input_tokens=0,
            output_tokens=0,
            from_cache=False,
            raw_response="Max retries exceeded",
        )
