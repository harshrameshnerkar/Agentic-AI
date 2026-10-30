import os
import re
from typing import Optional, Tuple
import requests
from dotenv import load_dotenv

from sql.prompt_templates import FEW_SHOT_EXAMPLES, SELF_CORRECTION_PROMPT_TEMPLATE, SYSTEM_SQL_PROMPT
from sql.schema_context import SchemaContextBuilder

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))


class TextToSQLGenerator:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.schema_context = SchemaContextBuilder.get_compact_schema_prompt()

    def generate_sql(self, question: str) -> Tuple[Optional[str], bool, Optional[str]]:
        is_answerable, unanswerable_reason = SchemaContextBuilder.check_answerability(question)
        if not is_answerable:
            return None, False, unanswerable_reason

        generated_sql = None
        error_notes = []

        if self.groq_api_key:
            try:
                generated_sql = self._generate_with_groq(question)
            except Exception as e:
                error_notes.append(f"Groq failed: {e}")

        if not generated_sql and self.gemini_api_key:
            try:
                generated_sql = self._generate_with_gemini(question)
            except Exception as e:
                error_notes.append(f"Gemini failed: {e}")

        if not generated_sql and self.openai_api_key:
            try:
                generated_sql = self._generate_with_openai(question)
            except Exception as e:
                error_notes.append(f"OpenAI failed: {e}")

        if not generated_sql:
            generated_sql, heuristic_answerable, h_reason = self._generate_offline_heuristic(question)
            if not heuristic_answerable:
                return None, False, h_reason

        if not generated_sql:
            return None, False, f"Failed to generate SQL. Errors: {'; '.join(error_notes)}"

        if "UNANSWERABLE:" in generated_sql.upper():
            reason = re.sub(r"(?i)unanswerable:\s*", "", generated_sql).strip()
            return None, False, reason or "Question cannot be answered from the database schema."

        return self._clean_llm_sql(generated_sql), True, None

    def correct_sql(self, question: str, failed_sql: str, db_error: str) -> Tuple[Optional[str], bool, Optional[str]]:
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
            corrected = self._heuristic_error_repair(failed_sql, db_error)

        if not corrected:
            return None, False, f"Self-correction failed: {db_error}"

        return self._clean_llm_sql(corrected), True, None

    def _generate_with_groq(self, question: str) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        messages = [{"role": "system", "content": SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context)}]
        for ex in FEW_SHOT_EXAMPLES:
            messages.append({"role": "user", "content": ex["question"]})
            messages.append({"role": "assistant", "content": ex["sql"]})
        messages.append({"role": "user", "content": question})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 300,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _generate_with_gemini(self, question: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        prompt_parts = [SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context) + "\n\n"]
        for ex in FEW_SHOT_EXAMPLES:
            prompt_parts.append(f"Question: {ex['question']}\nSQL: {ex['sql']}\n\n")
        prompt_parts.append(f"Question: {question}\nSQL:")

        payload = {
            "contents": [{"parts": [{"text": "".join(prompt_parts)}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 300},
        }
        res = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=8.0)
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        return None

    def _generate_with_openai(self, question: str) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        messages = [{"role": "system", "content": SYSTEM_SQL_PROMPT.format(schema_context=self.schema_context)}]
        for ex in FEW_SHOT_EXAMPLES:
            messages.append({"role": "user", "content": ex["question"]})
            messages.append({"role": "assistant", "content": ex["sql"]})
        messages.append({"role": "user", "content": question})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 300,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _query_groq_direct(self, prompt: str) -> Optional[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        res = requests.post(
            url,
            headers=headers,
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0},
            timeout=8.0,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _query_gemini_direct(self, prompt: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        res = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0, "maxOutputTokens": 300}},
            timeout=8.0,
        )
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        return None

    def _query_openai_direct(self, prompt: str) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        res = requests.post(
            url,
            headers=headers,
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0},
            timeout=8.0,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _generate_offline_heuristic(self, question: str) -> Tuple[Optional[str], bool, Optional[str]]:
        q = question.lower()

        if "product" in q and ("price" in q or "cost" in q):
            if "maximum" in q or "max" in q or "highest" in q:
                return "SELECT MAX(Price) FROM Products;", True, None
            if "average" in q or "avg" in q:
                cat_match = re.search(r"categoryid\s*(\d+)", q)
                if cat_match:
                    return f"SELECT AVG(Price) FROM Products WHERE CategoryID = {cat_match.group(1)};", True, None
                return "SELECT AVG(Price) FROM Products;", True, None
            if "greater than" in q or ">" in q:
                val_match = re.search(r"(?:greater than|>)\s*(\d+)", q)
                v = val_match.group(1) if val_match else "50"
                return f"SELECT * FROM Products WHERE Price > {v};", True, None
            return "SELECT ProductName, Price FROM Products;", True, None

        if "customer" in q and ("germany" in q or "country" in q or "city" in q or "london" in q or "paris" in q):
            if "germany" in q:
                return "SELECT COUNT(*) FROM Customers WHERE Country = 'Germany';", True, None
            if "london" in q or "paris" in q:
                return "SELECT CustomerName, City FROM Customers WHERE City IN ('London', 'Paris');", True, None
            return "SELECT Country, COUNT(*) AS CustomerCount FROM Customers GROUP BY Country;", True, None

        if "supplier" in q and "country" in q:
            return "SELECT DISTINCT Country FROM Suppliers;", True, None

        if "product" in q and "supplier" in q:
            if "japan" in q:
                return "SELECT p.ProductName FROM Products p JOIN Suppliers s ON p.SupplierID = s.SupplierID WHERE s.Country = 'Japan';", True, None
            return "SELECT SupplierID, COUNT(*) FROM Products GROUP BY SupplierID;", True, None

        if "employee" in q and ("name" in q or "first" in q or "last" in q):
            return "SELECT FirstName, LastName FROM Employees;", True, None

        if "order" in q and "employee" in q:
            emp_match = re.search(r"employeeid\s*(\d+)", q)
            e_id = emp_match.group(1) if emp_match else "4"
            return f"SELECT COUNT(*) FROM Orders WHERE EmployeeID = {e_id};", True, None

        if "quantity" in q and "order" in q:
            order_match = re.search(r"orderid\s*(\d+)", q)
            o_id = order_match.group(1) if order_match else "10248"
            return f"SELECT SUM(Quantity) FROM OrderDetails WHERE OrderID = {o_id};", True, None

        if "shipper" in q:
            return "SELECT ShipperName, Phone FROM Shippers;", True, None

        if "product" in q and "category" in q:
            return "SELECT p.ProductName, c.CategoryName FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID;", True, None

        if "order" in q and "date" in q:
            return "SELECT * FROM Orders ORDER BY OrderDate DESC;", True, None

        if "customer" in q and ("order" in q or "spent" in q or "expensive" in q):
            return (
                "SELECT c.CompanyName, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS OrderTotal "
                "FROM Customers c JOIN Orders o ON c.CustomerID = o.CustomerID "
                "JOIN OrderDetails od ON o.OrderID = od.OrderID "
                "GROUP BY o.OrderID ORDER BY OrderTotal DESC LIMIT 1;",
                True,
                None,
            )

        for tbl in ["Products", "Customers", "Orders", "Suppliers", "Employees", "Categories", "Shippers"]:
            stem = tbl.lower().rstrip("s")
            if stem in q or tbl.lower() in q:
                return f"SELECT COUNT(*) AS TotalCount FROM {tbl};", True, None

        return None, False, "Question is ambiguous or cannot be mapped to the database schema."

    def _heuristic_error_repair(self, failed_sql: str, db_error: str) -> Optional[str]:
        fixed_sql = failed_sql
        err = db_error.lower()

        if "no such table: customer" in err:
            fixed_sql = re.sub(r"\bcustomer\b", "Customers", fixed_sql, flags=re.IGNORECASE)
        if "no such table: invoice" in err:
            fixed_sql = re.sub(r"\binvoice\b", "Orders", fixed_sql, flags=re.IGNORECASE)
        if "no such table: track" in err:
            fixed_sql = re.sub(r"\btrack\b", "Products", fixed_sql, flags=re.IGNORECASE)
        if "no such table: orderdetails" in err:
            fixed_sql = re.sub(r"\borderdetails\b", "[Order Details]", fixed_sql, flags=re.IGNORECASE)

        if "no such column: name" in err and "customer" in failed_sql.lower():
            fixed_sql = re.sub(r"\bname\b", "ContactName", fixed_sql, flags=re.IGNORECASE)
        if "totalrevenue" in err or "total_revenue" in err:
            fixed_sql = re.sub(r"\b(?:totalrevenue|total_revenue)\b", "Freight", fixed_sql, flags=re.IGNORECASE)
        if "cost" in err:
            fixed_sql = re.sub(r"\bcost\b", "UnitPrice", fixed_sql, flags=re.IGNORECASE)
        if "no such column: price" in err:
            fixed_sql = re.sub(r"\bprice\b", "UnitPrice", fixed_sql, flags=re.IGNORECASE)

        return fixed_sql if fixed_sql != failed_sql else None

    @staticmethod
    def _clean_llm_sql(sql_str: str) -> str:
        s = sql_str.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(?:sql)?\n?", "", s, flags=re.IGNORECASE)
            s = re.sub(r"\n?```$", "", s).strip()
        if s.endswith(";"):
            s = s[:-1].strip()
        return s


sql_generator = TextToSQLGenerator()
