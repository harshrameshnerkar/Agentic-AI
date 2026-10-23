"""
Multi-Provider Text-to-SQL Generator for Role B (Data Service).

Translates natural language questions into valid SQL for the authentic Chinook
database with multi-provider LLM support (Groq, Gemini, OpenAI) and an offline fallback engine.
"""
import os
import re
from typing import Optional, Tuple
from dotenv import load_dotenv

from sql.prompt_templates import FEW_SHOT_EXAMPLES, SELF_CORRECTION_PROMPT_TEMPLATE, SYSTEM_SQL_PROMPT
from sql.schema_context import SchemaContextBuilder

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))


class TextToSQLGenerator:
    """Generates SQL queries from natural language with model fallback and answerability gates."""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.schema_context = SchemaContextBuilder.get_compact_schema_prompt()

    def generate_sql(self, question: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Translates a business question into SQL.

        Returns:
            (sql: Optional[str], answerable: bool, reason_or_error: Optional[str])
        """
        # 1. Semantic Domain & Answerability Pre-Check
        is_answerable, unanswerable_reason = SchemaContextBuilder.check_answerability(question)
        if not is_answerable:
            return None, False, unanswerable_reason

        # 2. Try LLM Generation (Groq -> Gemini -> OpenAI -> Offline Heuristic)
        generated_sql = None
        error_notes = []

        if self.groq_api_key:
            try:
                generated_sql = self._generate_with_groq(question)
            except Exception as e:
                error_notes.append(f"Groq generation failed: {str(e)}")

        if not generated_sql and self.gemini_api_key:
            try:
                generated_sql = self._generate_with_gemini(question)
            except Exception as e:
                error_notes.append(f"Gemini generation failed: {str(e)}")

        if not generated_sql and self.openai_api_key:
            try:
                generated_sql = self._generate_with_openai(question)
            except Exception as e:
                error_notes.append(f"OpenAI generation failed: {str(e)}")

        # 3. Fallback to offline rule-based heuristic if API calls are unavailable
        if not generated_sql:
            generated_sql, heuristic_answerable, h_reason = self._generate_offline_heuristic(question)
            if not heuristic_answerable:
                return None, False, h_reason

        if not generated_sql:
            return None, False, f"Failed to generate SQL for question. Errors: {'; '.join(error_notes)}"

        # 4. Check if LLM explicitly flagged the question as unanswerable
        if "UNANSWERABLE:" in generated_sql.upper():
            reason = re.sub(r"(?i)unanswerable:\s*", "", generated_sql).strip()
            return None, False, reason or "Question cannot be answered from the database schema."

        # Clean markdown codeblocks
        cleaned = self._clean_llm_sql(generated_sql)
        return cleaned, True, None

    def correct_sql(self, question: str, failed_sql: str, db_error: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Generates a corrected SQL query given the database runtime error.
        """
        prompt = SELF_CORRECTION_PROMPT_TEMPLATE.format(
            schema_context=self.schema_context,
            question=question,
            failed_sql=failed_sql,
            error_message=db_error,
        )

        corrected = None
        if self.groq_api_key:
            try:
                corrected = self._query_groq_direct(prompt)
            except Exception:
                pass

        if not corrected and self.gemini_api_key:
            try:
                corrected = self._query_gemini_direct(prompt)
            except Exception:
                pass

        if not corrected and self.openai_api_key:
            try:
                corrected = self._query_openai_direct(prompt)
            except Exception:
                pass

        if not corrected:
            # Deterministic heuristic repair for common errors
            corrected = self._heuristic_error_repair(failed_sql, db_error)

        if not corrected:
            return None, False, f"Self-correction failed to resolve error: {db_error}"

        cleaned = self._clean_llm_sql(corrected)
        return cleaned, True, None

    # --------------------------------------------------------------------------
    # LLM API Call Implementations
    # --------------------------------------------------------------------------
    def _generate_with_groq(self, question: str) -> Optional[str]:
        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context)}]
        for ex in FEW_SHOT_EXAMPLES:
            messages.append({"role": "user", "content": ex["question"]})
            messages.append({"role": "assistant", "content": ex["sql"]})
        messages.append({"role": "user", "content": question})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 400,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _query_groq_direct(self, prompt: str) -> Optional[str]:
        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 400,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _generate_with_gemini(self, question: str) -> Optional[str]:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        system_instruction = SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context)
        contents = [
            {"role": "user", "parts": [{"text": f"{system_instruction}\n\nQuestion: {question}\nGenerate SQL:"}]}
        ]
        payload = {"contents": contents, "generationConfig": {"temperature": 0.0, "maxOutputTokens": 400}}
        res = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    def _query_gemini_direct(self, prompt: str) -> Optional[str]:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0}}
        res = requests.post(url, json=payload, timeout=8.0)
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    def _generate_with_openai(self, question: str) -> Optional[str]:
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        messages = [
            {"role": "system", "content": SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context)},
            {"role": "user", "content": question},
        ]
        res = requests.post(url, headers=headers, json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.0}, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _query_openai_direct(self, prompt: str) -> Optional[str]:
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        res = requests.post(url, headers=headers, json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    # --------------------------------------------------------------------------
    # Offline Heuristic & Fallback Generation for Chinook
    # --------------------------------------------------------------------------
    def _generate_offline_heuristic(self, question: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """Rule-based pattern matcher for standard Chinook real enterprise questions."""
        q = question.lower()

        # 1. Top customers by invoices
        if "customer" in q and ("invoice" in q or "order" in q or "most" in q or "top" in q):
            limit_match = re.search(r"\b(\d+)\b", q)
            k = limit_match.group(1) if limit_match else "5"
            return (
                f"SELECT c.FirstName || ' ' || c.LastName AS CustomerName, COUNT(i.InvoiceId) AS InvoiceCount "
                f"FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
                f"GROUP BY c.CustomerId, CustomerName ORDER BY InvoiceCount DESC LIMIT {k};",
                True, None
            )

        # 2. Total revenue from all invoices
        if "total revenue" in q or "gross sales" in q or ("total" in q and ("invoice" in q or "sale" in q)):
            return (
                "SELECT ROUND(SUM(Total), 2) AS TotalRevenue FROM Invoice;",
                True, None
            )

        # 3. Top selling tracks / songs
        if ("track" in q or "song" in q or "music" in q) and ("top" in q or "best" in q or "selling" in q):
            limit_match = re.search(r"\b(\d+)\b", q)
            k = limit_match.group(1) if limit_match else "5"
            return (
                f"SELECT t.Name AS TrackName, SUM(il.Quantity) AS UnitsSold "
                f"FROM Track t JOIN InvoiceLine il ON t.TrackId = il.TrackId "
                f"GROUP BY t.TrackId, TrackName ORDER BY UnitsSold DESC LIMIT {k};",
                True, None
            )

        # 4. Customers by country
        if "customer" in q and "country" in q:
            return (
                "SELECT Country, COUNT(CustomerId) AS CustomerCount "
                "FROM Customer GROUP BY Country ORDER BY CustomerCount DESC;",
                True, None
            )

        # 5. Top artists by track count
        if "artist" in q and ("most" in q or "track" in q or "song" in q or "album" in q):
            return (
                "SELECT ar.Name AS ArtistName, COUNT(t.TrackId) AS TrackCount "
                "FROM Artist ar JOIN Album al ON ar.ArtistId = al.ArtistId "
                "JOIN Track t ON al.AlbumId = t.AlbumId "
                "GROUP BY ar.ArtistId, ar.Name ORDER BY TrackCount DESC LIMIT 5;",
                True, None
            )

        # 6. Employees / sales support reps
        if "employee" in q or "support rep" in q or "sales rep" in q or "staff" in q:
            return (
                "SELECT FirstName || ' ' || LastName AS EmployeeName, Title, City, Country "
                "FROM Employee;",
                True, None
            )

        # 7. Genres breakdown
        if "genre" in q:
            return (
                "SELECT g.Name AS GenreName, COUNT(t.TrackId) AS TrackCount "
                "FROM Genre g JOIN Track t ON g.GenreId = t.GenreId "
                "GROUP BY g.GenreId, g.Name ORDER BY TrackCount DESC;",
                True, None
            )

        # 8. Media Types
        if "media" in q:
            return "SELECT DISTINCT Name AS MediaTypeName FROM MediaType;", True, None

        # Default fallback: safe count query on most relevant table
        for tbl in ["Invoice", "Customer", "Employee", "Track", "Album", "Artist", "Genre", "MediaType"]:
            if tbl.lower() in q:
                return f"SELECT COUNT(*) AS TotalCount FROM {tbl};", True, None

        return None, False, "Question is ambiguous or cannot be mapped to the enterprise database schema."

    def _heuristic_error_repair(self, failed_sql: str, db_error: str) -> Optional[str]:
        """Repairs common column or table naming mistakes deterministically."""
        fixed_sql = failed_sql
        err = db_error.lower()

        # Fix column hallucinations:
        # e.g. "no such column: name" on Customer -> FirstName || ' ' || LastName
        if "no such column: name" in err and "customer" in failed_sql.lower():
            fixed_sql = re.sub(r"\bname\b", "FirstName || ' ' || LastName", fixed_sql, flags=re.IGNORECASE)

        if "totalrevenue" in err or "total_revenue" in err or "revenue" in err:
            fixed_sql = re.sub(r"\b(?:totalrevenue|total_revenue|revenue)\b", "Total", fixed_sql, flags=re.IGNORECASE)

        if "no such column: price" in err:
            fixed_sql = re.sub(r"\bprice\b", "UnitPrice", fixed_sql, flags=re.IGNORECASE)

        if fixed_sql != failed_sql:
            return fixed_sql
        return None

    @staticmethod
    def _clean_llm_sql(sql_str: str) -> str:
        s = sql_str.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(?:sql)?\n?", "", s, flags=re.IGNORECASE)
            s = re.sub(r"\n?```$", "", s)
            s = s.strip()
        if s.endswith(";"):
            s = s[:-1].strip()
        return s


# Shared singleton instance
sql_generator = TextToSQLGenerator()
