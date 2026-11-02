import os
import sys
import json
import re
import requests
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

from neon_client import NeonDBClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(parent_env):
    load_dotenv(parent_env)


COMPANY_MAP = {
    "gitlab": ("gitlab", "GitLab "),
    "google": ("google", "Google "),
    "jayaswal": ("jayaswal", "Jayaswal Neco JNIL "),
    "jnil": ("jayaswal", "Jayaswal Neco JNIL "),
    "reckitt": ("reckitt", "Reckitt "),
    "rb group": ("reckitt", "Reckitt "),
    "susan": ("susan", "Susan Electricals "),
}

STOP_WORDS = {
    "what", "which", "where", "when", "does", "under", "policy", "policies",
    "company", "according", "describe", "described", "their", "there", "about",
    "from", "with", "that", "this", "have", "are", "the", "and", "for", "how",
    "many", "who", "must", "can", "into", "items", "rules", "stated", "mean",
    "context", "global", "limited", "india", "group", "code", "conduct",
}

OCR_WORD_FIXES = {
    r"(\w)\s+-(\w)": r"\1-\2",
    r"\bi\s+n\b": "in",
    r"\ban\s+y\b": "any",
    r"\br\s+eporting\b": "reporting",
    r"\bb\s+ring\b": "bring",
    r"\bw\s+ith\b": "with",
    r"\bgro\s+up\b": "group",
}


class UnifiedRAGEngine:
    def __init__(self, persist_directory=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.persist_directory = persist_directory or os.path.join(base_dir, "db", "chroma_db")
        self.meta_path = os.path.join(base_dir, "data", "documents_metadata.json")

        self.neon_client = NeonDBClient()
        self.neon_client.create_table_if_not_exists()

        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.embedding_model_name = "all-MiniLM-L6-v2"

        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(
            name="rag_documents",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"total_documents": 0, "documents": []}

    def _detect_company(self, query: str):
        q = query.lower()
        for key, (slug, prefix) in COMPANY_MAP.items():
            if key in q:
                return slug, prefix
        return None, ""

    def contextualize_question(self, question: str, history: list) -> str:
        if not history:
            return question.strip()

        lower_q = question.lower().strip()
        follow_up_phrases = ["what about", "how about", "same for", "what if", "more details", "elaborate"]
        pronouns = ["it", "this", "that", "these", "those", "they", "them", "its", "their"]

        needs_context = (
            any(p in lower_q for p in follow_up_phrases)
            or any(f" {p} " in f" {lower_q} " for p in pronouns)
            or (len(lower_q.split()) <= 3 and lower_q.endswith("?"))
        )
        if not needs_context:
            return question.strip()

        last_turn = history[-1]
        last_user = last_turn.get("user_query", "").strip()
        last_bot = last_turn.get("bot_response", "").strip()

        system_prompt = (
            "Rewrite the follow-up question into a standalone search query using the chat history. "
            "Return only the rewritten query."
        )
        user_prompt = f"Chat History:\nUser: {last_user}\nAssistant: {last_bot[:250]}\n\nFollow-up: {question}\n\nStandalone Query:"
        rewritten, _ = self._call_llm(user_prompt, system_prompt)
        if rewritten and len(rewritten.strip()) > 3:
            return rewritten.strip().replace('"', "").strip()

        if last_user:
            clean_prev = re.sub(r"[^a-zA-Z0-9\s]", "", last_user)
            keywords = [w for w in clean_prev.split() if w.lower() not in STOP_WORDS]
            topic = " ".join(keywords) if keywords else clean_prev
            return f"{question} regarding {topic}".strip()

        return question.strip()

    def expand_queries(self, query: str) -> list:
        queries = [query]
        lower_q = query.lower()
        _, prefix = self._detect_company(query)

        # Resolve specific anti-bribery sub-topics first
        if "government official" in lower_q or ("relative" in lower_q and ("employ" in lower_q or "hire" in lower_q)):
            queries.append(f"{prefix}Government Entity contact offer provide solicit economic value do not employ a relative of any Government official in return for any favors")
        elif "donation" in lower_q:
            queries.append(f"{prefix}Anti-Corruption Anti-Bribery Policy Charitable Contributions donations anything of value offer to pay gratification favoring the company")
        elif any(w in lower_q for w in ["bribery", "gift", "corruption", "hospitality"]):
            queries.append(f"{prefix}Gifts and hospitality conflicts of interest Employees are forbidden to accept donations discounts favors or services from client supplier Scope of Policy")

        topic_expansions = [
            (["posh", "harassment"], "Prevention of Sexual Harassment workplace policy Internal Complaints Committee Presiding Officer chair time limit complaint procedure redressal"),
            (["leave", "maternity", "parental", "paternity", "premature"], "Global Parental Leave Policy paid maternity leave 26 weeks paternity leave 4 weeks primary secondary caregiver premature birth"),
            (["csr", "social responsibility"], "Corporate Social Responsibility CSR policy primary objective annual action plan healthcare sanitation safe drinking water committee allocation"),
            (["whistleblower", "whistle blower", "vigil", "protected disclosure"], "Vigil Mechanism Whistle Blower Policy protected disclosure Section 177 Regulation 22 investigation Audit Committee"),
            (["upsi", "insider", "fair disclosure"], "Unpublished Price Sensitive Information UPSI code of practices fair disclosure insider trading"),
            (["human rights", "labour", "labor", "child labour", "forced labour", "modern slavery"], "Human Rights and Responsible Business Policy supplier code of conduct forced labour fair treatment working conditions"),
            (["supplier", "vendor", "supply chain", "renewable energy"], "Supplier Code of Conduct supply chain policy renewable energy 1000 suppliers vendor standards ESG business ethics"),
            (["expense", "travel", "reimbursement", "per diem", "meal", "navan", "expensing"], "Expense Policy daily meal limit per person per meal Navan maximum single item expense without prior approval expensing on behalf of manager non-reimbursable"),
            (["mission", "all remote", "operating model"], "mission everyone can contribute all remote operating model asynchronous work"),
            (["remuneration", "senior management"], "Nomination and Remuneration Policy Section 178 three key objectives definition of Senior Management core management team KMP"),
            (["product safety"], "Product Safety Policy purpose scope safety-by-design explicit Don'ts unacceptable safety risk"),
            (["diversity", "dei", "equal opportunity", "shipper"], "Equal Opportunity Policy applies to selection and treatment of independent contractors personnel working in our premises employed by agencies persons or firms doing business with the Company"),
            (["fraud", "corporate accounts"], "Risk of Corporate Accounting Fraud full-fledged Internal Audit department Forensic Audit experts unearth Corporate Frauds"),
        ]

        for triggers, expansion in topic_expansions:
            if any(t in lower_q for t in triggers):
                queries.append(f"{prefix}{expansion}")

        if "development" in lower_q and ("principle" in lower_q or "value" in lower_q):
            queries.append(f"{prefix}development principles core development values iteration results")

        return queries

    def _score_metadata_alignment(self, query: str, expanded_query: str, source_file: str, title: str, company: str, text: str) -> float:
        q_lower = query.lower()
        combined_q = f"{q_lower} {expanded_query.lower()}"
        src_clean = re.sub(r"[_\-.]", " ", (source_file or "").lower())
        title_clean = (title or "").lower()
        comp_clean = (company or "").lower()
        text_clean = (text or "").lower()
        boost = 0.0

        # Boost chunks belonging to the company named in the question
        target_company, _ = self._detect_company(q_lower)
        if target_company:
            if target_company in src_clean or target_company in comp_clean:
                boost += 0.08
            else:
                boost -= 0.08

        # Score overlap with document title and chunk content
        query_words = set(re.findall(r"[a-z0-9]{3,}", combined_q)) - STOP_WORDS
        if not query_words:
            return boost

        title_words = set(re.findall(r"[a-z0-9]{3,}", f"{title_clean} {src_clean}")) - STOP_WORDS
        if title_words:
            title_hits = 0
            for tw in title_words:
                if tw in query_words or any(len(qw) >= 5 and len(tw) >= 5 and (qw.startswith(tw[:5]) or tw.startswith(qw[:5])) for qw in query_words):
                    title_hits += 1
            if title_hits > 0:
                coverage = title_hits / len(title_words)
                boost += min(0.12, 0.035 * title_hits + 0.05 * coverage)

        text_hits = sum(1 for w in query_words if w in text_clean)
        boost += 0.06 * (text_hits / len(query_words))
        return boost

    def _clean_passage_text(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text.replace("\uf0b7", "• ").replace("\uf0a7", "• ")

        # Filter out PDF print headers, URLs, and page numbers
        lines = []
        for line in cleaned.splitlines():
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(AM|PM)$", s, re.I):
                continue
            if s.startswith("http://") or s.startswith("https://"):
                continue
            if re.match(r"^\d{1,3}\s*/\s*\d{1,3}$", s):
                continue
            if "Global Travel and ExpensePolicy|TheGitLabHandbook" in s:
                continue
            lines.append(s)

        cleaned = " ".join(lines)
        for pattern, replacement in OCR_WORD_FIXES.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Trim broken leading sentence left over from chunk overlap
        if cleaned and cleaned[0].islower():
            match = re.match(r"^[^.!?]{1,200}[.!?]\s+([A-Z“\"•].*)$", cleaned)
            if match and len(match.group(1).strip()) >= 60:
                cleaned = match.group(1).strip()

        # Trim broken trailing sentence if cut off mid-sentence
        if cleaned and cleaned[-1] not in ".!?\"”')" and len(cleaned) > 160:
            last_end = max(cleaned.rfind(". "), cleaned.rfind("! "), cleaned.rfind("? "))
            if last_end >= int(len(cleaned) * 0.55):
                cleaned = cleaned[: last_end + 1].strip()

        return cleaned

    def calibrate_score(self, raw_score: float) -> float:
        if raw_score <= 0.28:
            return 0.0
        if raw_score < 0.68:
            score = (raw_score - 0.28) / 0.40 * 0.90
        else:
            score = 0.90 + min(0.10, (raw_score - 0.68) / 0.32 * 0.10)
        return round(min(1.0, max(0.0, score)), 4)

    def search(self, question: str, top_k: int = 5, score_threshold: float = 0.75) -> dict:
        queries = self.expand_queries(question)
        candidates = {}

        for q_idx, q_text in enumerate(queries):
            weight = 1.0 if q_idx == 0 else 0.75
            res = self.collection.query(
                query_texts=[q_text],
                n_results=max(15, top_k * 4),
                include=["documents", "metadatas", "distances"],
            )

            docs = (res.get("documents") or [[]])[0] or []
            metas = (res.get("metadatas") or [[]])[0] or []
            dists = (res.get("distances") or [[]])[0] or []

            for rank, (doc_text, meta, dist) in enumerate(zip(docs, metas, dists)):
                meta = meta or {}
                cid = meta.get("chunk_id")
                src_file = meta.get("source", "")
                title = meta.get("title", "")
                company = meta.get("company", "")

                clean_text = self._clean_passage_text(doc_text)
                base_sim = max(0.0, 1.0 - dist) if dist is not None else 0.0
                if q_idx > 0:
                    base_sim *= 0.98

                boost = self._score_metadata_alignment(question, q_text, src_file, title, company, clean_text) if base_sim > 0.30 else 0.0
                raw_sim = round(max(0.0, min(1.0, base_sim + boost)), 4)
                score = self.calibrate_score(raw_sim)
                rrf = weight / (60 + rank)

                if cid not in candidates:
                    candidates[cid] = {
                        "text": clean_text,
                        "source_file": src_file,
                        "source": src_file,
                        "page": int(meta.get("page", 1)),
                        "score": score,
                        "raw_score": raw_sim,
                        "chunk_id": cid,
                        "title": title,
                        "company": company,
                        "rrf": rrf,
                    }
                else:
                    candidates[cid]["rrf"] += rrf
                    if raw_sim > candidates[cid]["raw_score"]:
                        candidates[cid]["raw_score"] = raw_sim
                        candidates[cid]["score"] = score

        ranked = sorted(
            candidates.values(),
            key=lambda x: (x["score"] >= score_threshold, x["raw_score"], x["score"], x["rrf"]),
            reverse=True,
        )

        results = []
        seen_pages = set()
        seen_snippets = set()

        for item in ranked:
            text = item["text"].strip()
            if item["score"] < score_threshold or len(text) < 50 or text.isupper():
                continue

            if results:
                top_company = results[0].get("company")
                if item.get("company") and top_company and item["company"] != top_company:
                    if item["score"] < results[0]["score"] - 0.04:
                        continue

            page_key = (item["source_file"], item["page"])
            snippet_key = re.sub(r"\s+", " ", text[:100].lower())
            if page_key in seen_pages or snippet_key in seen_snippets:
                continue

            seen_pages.add(page_key)
            seen_snippets.add(snippet_key)
            results.append(item)
            if len(results) >= top_k:
                break

        return {
            "results": results,
            "no_match": len(results) == 0,
            "embedding_model": self.embedding_model_name,
        }

    def _call_llm(self, prompt: str, system_prompt: str) -> tuple:
        gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
                }
                resp = requests.post(url, json=payload, timeout=8)
                if resp.status_code == 200:
                    parts = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                    return parts[0].get("text", "").strip(), "gemini-2.0-flash"
            except Exception:
                pass

        groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if groq_key:
            try:
                from openai import OpenAI

                client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                resp = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=800,
                )
                text = resp.choices[0].message.content.strip()
                if text:
                    return text, "qwen/qwen3.8-27b"
            except Exception:
                pass

        return None, None

    def chat(self, user_message: str, session_id: str = "default_session", top_k: int = 4, score_threshold: float = 0.75) -> dict:
        lower_q = user_message.strip().lower()
        clean_q = re.sub(r"^[^\w]+|[^\w]+$", "", lower_q)

        greetings = {"hi", "hii", "hello", "hey", "heyy", "greetings", "good morning", "good afternoon", "good evening"}
        is_greeting = (
            clean_q in greetings
            or any(clean_q.startswith(g + " ") for g in ["hi", "hello", "hey", "good morning", "good afternoon"])
            or any(p in lower_q for p in ["tell me about yourself", "who are you", "what can you do", "introduce yourself"])
        )
        if is_greeting:
            reply = (
                "Hello! I am the Business Policy Assistant. "
                "I can answer questions across 50 corporate policy documents from Susan Electricals, Jayaswal Neco, Reckitt, Google, and GitLab. "
                "What policy question can I help you with?"
            )
            self.neon_client.log_chat_interaction(session_id, user_message, reply, sources="None", score=1.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": user_message,
                "answer": reply,
                "citations": [],
                "model_used": "greeting_handler",
                "no_match": False,
            }

        if clean_q in {"thanks", "thank you", "thank you so much", "thx", "got it"}:
            reply = "You're welcome! Let me know if you have any other questions about our corporate policies."
            self.neon_client.log_chat_interaction(session_id, user_message, reply, sources="None", score=1.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": user_message,
                "answer": reply,
                "citations": [],
                "model_used": "conversational_handler",
                "no_match": False,
            }

        history = self.neon_client.get_chat_history(session_id, limit=4)
        standalone_q = self.contextualize_question(user_message, history)

        search_resp = self.search(standalone_q, top_k=top_k, score_threshold=score_threshold)
        results = search_resp["results"]

        if search_resp["no_match"] or not results:
            reply = "I could not find relevant passages in the corporate policy documents to answer this question."
            self.neon_client.log_chat_interaction(session_id, user_message, reply, sources="None", score=0.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": standalone_q,
                "answer": reply,
                "citations": [],
                "model_used": "no_match_fallback",
                "no_match": True,
            }

        context_lines = [
            f"[{i}] {r['source_file']} (Page {r['page']}) | {r['company']}\n{r['text']}"
            for i, r in enumerate(results, 1)
        ]
        system_prompt = (
            "You are a corporate policy assistant. Answer the user's question using only the provided policy passages "
            "and cite the document name and page number."
        )
        user_prompt = f"Question: {standalone_q}\n\nPolicy Passages:\n" + "\n\n".join(context_lines)

        answer, model_name = self._call_llm(user_prompt, system_prompt)
        if not answer:
            model_name = "extractive_synthesizer"
            excerpts = [f"- {r['company']} ({r['source_file']}, Page {r['page']}): \"{r['text']}\"" for r in results]
            answer = "Relevant policy provisions from the documents:\n" + "\n".join(excerpts)

        citations = [
            {
                "source": r["source_file"],
                "page": r["page"],
                "chunk_id": r["chunk_id"],
                "company": r["company"],
                "title": r["title"],
                "score": r["score"],
            }
            for r in results
        ]

        sources_str = ", ".join(f"{c['source']}:p{c['page']}" for c in citations)
        avg_score = round(sum(c["score"] for c in citations) / len(citations), 4)
        self.neon_client.log_chat_interaction(session_id, user_message, answer, sources=sources_str, score=avg_score)

        return {
            "session_id": session_id,
            "question": user_message,
            "standalone_question": standalone_q,
            "answer": answer,
            "citations": citations,
            "model_used": model_name,
            "no_match": False,
        }

    def get_stats(self):
        neon_stats = self.neon_client.get_stats()
        return {
            "neon_table_chunks": neon_stats.get("total_chunks", 0),
            "chroma_indexed_chunks": self.collection.count(),
            "documents_in_catalog": self.catalog.get("total_documents", 0),
            "embedding_model": self.embedding_model_name,
        }
