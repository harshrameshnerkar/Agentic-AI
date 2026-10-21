"""Structured Document Extractor for Commercial Invoices.

Responsibilities:
- Obtains candidate raw values from documents (via prompt + multimodal LLM or deterministic cache).
- Formulates multi-modal prompts (text vs image vs scanned PDF).
- Delegates candidate type checking, constraint checking, and business rule validation to InvoiceValidator.
- Coordinates the automated self-healing retry loop: feeds validator diagnostics back to the model.
- Emits structured InvoiceExtraction and ExtractionMetadata.
"""

from __future__ import annotations
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import dotenv
import openai

from src.schemas import CurrencyEnum, DocumentContent, InvoiceExtraction, PaymentTermsEnum
from src.validator import InvoiceValidator, ValidationResult

dotenv.load_dotenv()

SYSTEM_EXTRACTION_PROMPT = """You are an expert financial document extraction engine for commercial invoices and bills.
Your job is to extract candidate values for exactly 11 structured fields from the provided invoice document (text or image).

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
    """Obtains candidate invoice extractions and coordinates with InvoiceValidator."""

    def __init__(
        self,
        validator: Optional[InvoiceValidator] = None,
        cache_path: Optional[Union[str, Path]] = None,
        max_retries: int = 3,
        model: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.validator = validator or InvoiceValidator()
        self.cache_path = Path(cache_path) if cache_path else base_dir / "data" / "extractions_cache.json"
        self.max_retries = max_retries
        self.model = model or os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

        # Configure LLM Client (OpenAI-compatible or Gemini)
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or "dummy"
        base_url = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
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

    def obtain_candidate_json(self, messages: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any], int, int]:
        """Calls the model to obtain raw candidate JSON response text and parsed dict."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        usage = getattr(response, "usage", None)
        in_tokens = getattr(usage, "prompt_tokens", 0) or 0
        out_tokens = getattr(usage, "completion_tokens", 0) or 0

        raw_content = response.choices[0].message.content or "{}"
        cleaned_json = raw_content.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json)

        parsed_dict = json.loads(cleaned_json)
        return raw_content, parsed_dict, in_tokens, out_tokens

    def extract(
        self,
        doc: DocumentContent,
        force_fresh: bool = False,
    ) -> Tuple[InvoiceExtraction, ExtractionMetadata]:
        """Obtains candidate invoice fields, validates via InvoiceValidator, and retries if needed."""
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
            candidate_raw = cached_entry["extracted_data"]
            # Validate candidate from cache
            val_result = self.validator.validate_candidate_dict(candidate_raw)
            extraction = val_result.extraction or InvoiceExtraction.model_validate(candidate_raw)
            meta_dict = cached_entry.get("metadata", {})
            metadata = ExtractionMetadata(
                document_id=doc.document_id,
                model=meta_dict.get("model", self.model),
                latency_ms=meta_dict.get("latency_ms", 5.0),
                retries_used=meta_dict.get("retries_used", 0),
                validation_passed=val_result.is_valid,
                input_tokens=meta_dict.get("input_tokens", 350),
                output_tokens=meta_dict.get("output_tokens", 120),
                from_cache=True,
                raw_response=meta_dict.get("raw_response", ""),
            )
            return extraction, metadata

        # Prepare messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT}
        ]

        if doc.doc_type == "pdf_text" and doc.text.strip():
            user_msg = f"Extract candidate invoice fields from the following invoice document text:\n\n---\n{doc.text}\n---"
            messages.append({"role": "user", "content": user_msg})
        elif doc.image_base64:
            user_content = [
                {"type": "text", "text": "Extract candidate invoice fields from this invoice document image:"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{doc.image_base64}"}}
            ]
            if doc.text.strip():
                user_content.append({"type": "text", "text": f"Accompanying OCR/text snippets:\n{doc.text}"})
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": f"Document '{doc.filename}' has no text or image stream."})

        retries_used = 0
        total_in_tokens = 0
        total_out_tokens = 0
        last_raw_response = ""

        # Self-healing loop: Extractor queries model; Validator evaluates candidate
        for attempt in range(self.max_retries + 1):
            try:
                raw_resp, candidate_dict, in_tok, out_tok = self.obtain_candidate_json(messages)
                last_raw_response = raw_resp
                total_in_tokens += in_tok
                total_out_tokens += out_tok

                # Validator inspects types, constraints, and business rules
                val_result: ValidationResult = self.validator.validate_candidate_dict(candidate_dict)

                if not val_result.is_valid:
                    retries_used += 1
                    if attempt < self.max_retries:
                        # Feed validator feedback to the LLM
                        retry_feedback = val_result.get_retry_prompt_feedback()
                        messages.append({"role": "assistant", "content": last_raw_response})
                        messages.append({"role": "user", "content": retry_feedback})
                        continue
                    else:
                        # Retries exhausted
                        elapsed_ms = round((time.time() - start_time) * 1000, 2)
                        extraction = val_result.extraction or InvoiceExtraction()
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
                        return extraction, metadata

                # Successful validation
                extraction = val_result.extraction or InvoiceExtraction.model_validate(candidate_dict)
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

                # Persist to cache
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

            except Exception as err:
                retries_used += 1
                if attempt < self.max_retries:
                    messages.append({"role": "assistant", "content": last_raw_response})
                    messages.append({
                        "role": "user",
                        "content": f"JSON parsing failed with error: {str(err)}. Please return a single valid JSON object."
                    })
                else:
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
                        raw_response=str(err),
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
