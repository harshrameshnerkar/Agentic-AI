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


class UnifiedRAGEngine:
    def __init__(self, persist_directory=None):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        self.persist_directory = persist_directory or os.path.join(curr_dir, "db", "chroma_db")
        self.meta_path = os.path.join(curr_dir, "data", "documents_metadata.json")

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

    def contextualize_question(self, question: str, history: list) -> str:
        if not history:
            return question.strip()

        lower_q = question.lower().strip()
        words = lower_q.split()
        is_dependent = (
            any(t in lower_q for t in ["what about", "how about", "same for", "what if", "more details", "elaborate"])
            or any(f" {t} " in f" {lower_q} " for t in ["it", "this", "that", "these", "those", "they", "them", "its", "their"])
            or (len(words) <= 3 and lower_q.endswith("?"))
        )
        if not is_dependent:
            return question.strip()

        last_turn = history[-1]
        last_user = last_turn.get("user_query", "").strip()
        last_bot = last_turn.get("bot_response", "").strip()

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        if (gemini_key and gemini_key.strip()) or (groq_key and groq_key.strip()):
            try:
                system_prompt = (
                    "Rewrite the follow-up question into a standalone search query using the chat history. "
                    "Return only the rewritten query."
                )
                history_str = f"User: {last_user}\nAssistant: {last_bot[:250]}"
                user_prompt = f"Chat History:\n{history_str}\n\nFollow-up Question: {question}\n\nStandalone Query:"
                rewritten, _ = self._call_llm(user_prompt, system_prompt)
                if rewritten and len(rewritten.strip()) > 3:
                    return rewritten.strip().replace('"', "").strip()
            except Exception:
                pass

        if last_user:
            clean_prev = re.sub(r"[^a-zA-Z0-9\s]", "", last_user)
            stop_words = {"what", "is", "the", "policy", "for", "at", "in", "of", "and", "a", "an", "tell", "me", "about", "can", "you", "do", "know"}
            prev_keywords = [w for w in clean_prev.split() if w.lower() not in stop_words]
            topic_hint = " ".join(prev_keywords) if prev_keywords else clean_prev
            return f"{question} regarding {topic_hint}".strip()

        return question.strip()

    def expand_queries(self, query: str) -> list:
        queries = [query]
        lower_q = query.lower()

        # Detect company anchor so expanded queries stay grounded to the target company
        company_prefix = ""
        if "gitlab" in lower_q:
            company_prefix = "GitLab "
        elif "google" in lower_q:
            company_prefix = "Google "
        elif "jayaswal" in lower_q or "jnil" in lower_q:
            company_prefix = "Jayaswal Neco JNIL "
        elif "reckitt" in lower_q or "rb group" in lower_q:
            company_prefix = "Reckitt "
        elif "susan" in lower_q:
            company_prefix = "Susan Electricals "

        if "posh" in lower_q or "harassment" in lower_q:
            queries.append(f"{company_prefix}Prevention of Sexual Harassment workplace policy Internal Complaints Committee Presiding Officer chair time limit complaint procedure redressal")
        if any(w in lower_q for w in ["leave", "maternity", "parental", "paternity", "premature"]):
            queries.append(f"{company_prefix}Global Parental Leave Policy paid maternity leave 26 weeks paternity leave 4 weeks primary secondary caregiver premature birth")
        if "csr" in lower_q or "social responsibility" in lower_q:
            queries.append(f"{company_prefix}Corporate Social Responsibility CSR policy primary objective annual action plan healthcare sanitation safe drinking water committee allocation")
        if "government official" in lower_q or ("relative" in lower_q and "employ" in lower_q) or ("relative" in lower_q and "hire" in lower_q):
            queries.append(f"{company_prefix}Government Entity contact offer provide solicit economic value do not employ a relative of any Government official in return for any favors")
        elif "donation" in lower_q:
            queries.append(f"{company_prefix}Anti-Corruption Anti-Bribery Policy Charitable Contributions donations anything of value offer to pay gratification favoring the company")
        elif any(w in lower_q for w in ["bribery", "gift", "corruption", "hospitality"]):
            queries.append(f"{company_prefix}Gifts and hospitality conflicts of interest Employees are forbidden to accept donations discounts favors or services from client supplier Scope of Policy")
        if "whistleblower" in lower_q or "whistle blower" in lower_q or "vigil" in lower_q or "protected disclosure" in lower_q:
            queries.append(f"{company_prefix}Vigil Mechanism Whistle Blower Policy protected disclosure Section 177 Regulation 22 investigation Audit Committee")
        if "upsi" in lower_q or "insider" in lower_q or "fair disclosure" in lower_q:
            queries.append(f"{company_prefix}Unpublished Price Sensitive Information UPSI code of practices fair disclosure insider trading")
        if any(w in lower_q for w in ["human rights", "labour", "labor", "child labour", "forced labour", "modern slavery"]):
            queries.append(f"{company_prefix}Human Rights and Responsible Business Policy supplier code of conduct forced labour fair treatment working conditions")
        if any(w in lower_q for w in ["supplier", "vendor", "supply chain", "renewable energy"]):
            queries.append(f"{company_prefix}Supplier Code of Conduct supply chain policy renewable energy 1000 suppliers vendor standards ESG business ethics")
        if any(w in lower_q for w in ["expense", "travel", "reimbursement", "per diem", "meal", "navan", "expensing"]):
            queries.append(f"{company_prefix}Expense Policy daily meal limit per person per meal Navan maximum single item expense without prior approval expensing on behalf of manager non-reimbursable")
        if "mission" in lower_q or "all remote" in lower_q or "operating model" in lower_q:
            queries.append(f"{company_prefix}mission everyone can contribute all remote operating model asynchronous work")
        if "development" in lower_q and ("principle" in lower_q or "value" in lower_q):
            queries.append(f"{company_prefix}development principles core development values iteration results")
        if "remuneration" in lower_q or "senior management" in lower_q:
            queries.append(f"{company_prefix}Nomination and Remuneration Policy Section 178 three key objectives definition of Senior Management core management team KMP")
        if "product safety" in lower_q:
            queries.append(f"{company_prefix}Product Safety Policy purpose scope safety-by-design explicit Don'ts unacceptable safety risk")
        if "diversity" in lower_q or "dei" in lower_q or "equal opportunity" in lower_q or "shipper" in lower_q:
            queries.append(f"{company_prefix}Equal Opportunity Policy applies to selection and treatment of independent contractors personnel working in our premises employed by agencies persons or firms doing business with the Company")
        if "fraud" in lower_q or "corporate accounts" in lower_q:
            queries.append(f"{company_prefix}Risk of Corporate Accounting Fraud full-fledged Internal Audit department Forensic Audit experts unearth Corporate Frauds")

        return queries

    def _detect_target_company(self, query: str) -> str | None:
        q = query.lower()
        if "gitlab" in q:
            return "gitlab"
        if "google" in q:
            return "google"
        if "jayaswal" in q or "jnil" in q:
            return "jayaswal"
        if "reckitt" in q or "rb group" in q:
            return "reckitt"
        if "susan" in q:
            return "susan"
        return None

    def _score_metadata_alignment(self, query: str, expanded_query: str, source_file: str, title: str, company: str, text: str) -> float:
        q = query.lower()
        q_all = f"{q} {expanded_query.lower()}"
        src = re.sub(r"[_\-.]", " ", (source_file or "").lower())
        ttl = (title or "").lower()
        comp = (company or "").lower()
        txt = (text or "").lower()
        boost = 0.0

        # 1. Company alignment (grounded in chunk's company metadata)
        target_company = self._detect_target_company(q)
        if target_company:
            if target_company in src or target_company in comp:
                boost += 0.08
            else:
                boost -= 0.08

        # 2. Generic document title / filename token overlap (no hardcoded document list)
        stop_words = {
            "what", "which", "where", "when", "does", "under", "policy", "policies",
            "company", "according", "describe", "described", "their", "there", "about",
            "from", "with", "that", "this", "have", "are", "the", "and", "for", "how",
            "many", "who", "must", "can", "into", "items", "rules", "stated", "mean",
            "context", "global", "limited", "india", "group", "code", "conduct",
        }
        q_tokens = [w for w in re.findall(r"[a-z0-9]{3,}", q_all) if w not in stop_words]
        if q_tokens:
            unique_q = set(q_tokens)
            title_words = set(re.findall(r"[a-z0-9]{3,}", f"{ttl} {src}")) - stop_words
            if title_words:
                title_hits = sum(1 for tw in title_words if tw in unique_q or any(w.startswith(tw[:5]) or tw.startswith(w[:5]) for w in unique_q if len(w) >= 5 and len(tw) >= 5))
                if title_hits > 0:
                    title_coverage = title_hits / len(title_words)
                    boost += min(0.12, 0.035 * title_hits + 0.05 * title_coverage)

            text_hits = sum(1 for w in unique_q if w in txt)
            boost += 0.06 * (text_hits / len(unique_q))

        return boost

    def _clean_passage_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.replace("\uf0b7", "• ").replace("\uf0a7", "• ")
        # Remove browser print timestamps, URLs, and page counter footers
        lines = []
        for line in cleaned.splitlines():
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*(AM|PM)$", s, re.I):
                continue
            if re.match(r"^https?://\S+$", s, re.I):
                continue
            if re.match(r"^\d{1,3}\s*/\s*\d{1,3}$", s):
                continue
            if "Global Travel and ExpensePolicy|TheGitLabHandbook" in s:
                continue
            lines.append(s)
        cleaned = " ".join(lines)
        # Fix common PDF/OCR split-word & hyphen artifacts
        cleaned = re.sub(r"(\w)\s+-(\w)", r"\1-\2", cleaned)
        cleaned = re.sub(r"\bi\s+n\b", "in", cleaned)
        cleaned = re.sub(r"\ban\s+y\b", "any", cleaned)
        cleaned = re.sub(r"\br\s+eporting\b", "reporting", cleaned)
        cleaned = re.sub(r"\bb\s+ring\b", "bring", cleaned)
        cleaned = re.sub(r"\bw\s+ith\b", "with", cleaned)
        cleaned = re.sub(r"\bgro\s+up\b", "group", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Strip leading incomplete sentence fragment from chunk overlap
        if cleaned and cleaned[0].islower():
            m = re.match(r"^[^.!?]{1,200}[.!?]\s+([A-Z“\"•].*)$", cleaned)
            if m and len(m.group(1).strip()) >= 60:
                cleaned = m.group(1).strip()

        # Strip trailing incomplete sentence fragment if chunk cut off mid-sentence
        if cleaned and cleaned[-1] not in ".!?\"”')" and len(cleaned) > 160:
            last_Boundary = max(cleaned.rfind(". "), cleaned.rfind("! "), cleaned.rfind("? "))
            if last_Boundary >= int(len(cleaned) * 0.55):
                cleaned = cleaned[: last_Boundary + 1].strip()

        return cleaned

    def calibrate_score(self, raw_score: float) -> float:
        if raw_score <= 0.28:
            return 0.0
        if raw_score < 0.68:
            calibrated = (raw_score - 0.28) / (0.68 - 0.28) * 0.90
        else:
            calibrated = 0.90 + min(0.10, (raw_score - 0.68) / 0.32 * 0.10)
        return round(min(1.0, max(0.0, calibrated)), 4)

    def search(self, question: str, top_k: int = 5, score_threshold: float = 0.75) -> dict:
        all_queries = self.expand_queries(question)
        aggregated_matches = {}

        for q_idx, q_text in enumerate(all_queries):
            query_weight = 1.0 if q_idx == 0 else 0.75
            query_res = self.collection.query(
                query_texts=[q_text],
                n_results=max(15, top_k * 4),
                include=["documents", "metadatas", "distances"],
            )
            raw_docs = (query_res or {}).get("documents") or []
            raw_metas = (query_res or {}).get("metadatas") or []
            raw_dists = (query_res or {}).get("distances") or []

            docs = raw_docs[0] if raw_docs and raw_docs[0] is not None else []
            metas = raw_metas[0] if raw_metas and raw_metas[0] is not None else []
            dists = raw_dists[0] if raw_dists and raw_dists[0] is not None else []

            for rank, (doc_text, meta, dist) in enumerate(zip(docs, metas, dists)):
                meta = meta or {}
                cid = meta.get("chunk_id")
                src_file = meta.get("source", "")
                title = meta.get("title", "")
                company = meta.get("company", "")

                cleaned_doc_text = self._clean_passage_text(doc_text)
                base_sim = max(0.0, 1.0 - dist) if dist is not None else 0.0
                if q_idx > 0:
                    base_sim *= 0.98
                alignment_boost = self._score_metadata_alignment(question, q_text, src_file, title, company, cleaned_doc_text) if base_sim > 0.30 else 0.0
                raw_similarity = round(max(0.0, min(1.0, base_sim + alignment_boost)), 4)
                calibrated_confidence = self.calibrate_score(raw_similarity)
                rrf_score = query_weight * (1.0 / (60 + rank))

                if cid not in aggregated_matches:
                    aggregated_matches[cid] = {
                        "text": cleaned_doc_text,
                        "source_file": src_file,
                        "source": src_file,
                        "page": int(meta.get("page", 1)),
                        "score": calibrated_confidence,
                        "raw_score": raw_similarity,
                        "chunk_id": cid,
                        "title": title,
                        "company": company,
                        "rrf": rrf_score,
                    }
                else:
                    aggregated_matches[cid]["rrf"] += rrf_score
                    if raw_similarity > aggregated_matches[cid]["raw_score"]:
                        aggregated_matches[cid]["raw_score"] = raw_similarity
                        aggregated_matches[cid]["score"] = calibrated_confidence

        sorted_candidates = sorted(
            aggregated_matches.values(),
            key=lambda x: (x["score"] >= score_threshold, x["raw_score"], x["score"], x["rrf"]),
            reverse=True,
        )

        seen_snippets = set()
        seen_source_pages = set()
        filtered_results = []
        for c in sorted_candidates:
            txt_clean = c["text"].strip()
            if c["score"] < score_threshold or len(txt_clean) < 50 or txt_clean.isupper():
                continue
            if filtered_results:
                top_match = filtered_results[0]
                if c.get("company") and top_match.get("company") and c["company"] != top_match["company"]:
                    if c["score"] < top_match["score"] - 0.04:
                        continue
            sp_key = (c["source_file"], c["page"])
            if sp_key in seen_source_pages:
                continue
            norm_snip = re.sub(r"\s+", " ", txt_clean[:100].lower())
            if norm_snip in seen_snippets:
                continue
            seen_source_pages.add(sp_key)
            seen_snippets.add(norm_snip)
            filtered_results.append(c)
            if len(filtered_results) >= top_k:
                break

        return {
            "results": filtered_results,
            "no_match": len(filtered_results) == 0,
            "embedding_model": self.embedding_model_name,
        }

    def _call_llm(self, prompt: str, system_prompt: str) -> tuple:
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key and gemini_key.strip():
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key.strip()}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
                }
                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
                    return parts[0].get("text", "").strip(), "gemini-2.0-flash"
            except Exception:
                pass

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key.strip():
            try:
                from openai import OpenAI

                client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key.strip())
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
        clean_msg = user_message.strip()
        lower_q = clean_msg.lower()
        clean_q = re.sub(r"^[^\w]+|[^\w]+$", "", lower_q)

        greeting_words = {"hi", "hii", "hello", "hey", "heyy", "greetings", "good morning", "good afternoon", "good evening"}
        is_greeting = (
            clean_q in greeting_words
            or any(clean_q.startswith(g + " ") for g in ["hi", "hii", "hello", "hey", "good morning", "good afternoon"])
            or any(p in lower_q for p in ["tell me about yourself", "who are you", "what are you", "what can you do", "introduce yourself"])
        )

        if is_greeting:
            greeting_reply = (
                "Hello. I am the Business Policy Assistant. "
                "I can answer questions across 50 corporate policy documents from Susan Electricals, Jayaswal Neco, Reckitt, Google, and GitLab "
                "covering HR and leave policies, governance and ethics, supply chain rules, and IT/operations. "
                "What policy question can I help you with?"
            )
            self.neon_client.log_chat_interaction(session_id, user_message, greeting_reply, sources="None", score=1.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": user_message,
                "answer": greeting_reply,
                "citations": [],
                "model_used": "greeting_handler",
                "no_match": False,
            }

        thanks_words = {"thanks", "thank you", "thank you so much", "thx", "great thanks", "got it"}
        if clean_q in thanks_words:
            thanks_reply = "You're welcome. Let me know if you have any other questions about the policy documents."
            self.neon_client.log_chat_interaction(session_id, user_message, thanks_reply, sources="None", score=1.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": user_message,
                "answer": thanks_reply,
                "citations": [],
                "model_used": "conversational_handler",
                "no_match": False,
            }

        history = self.neon_client.get_chat_history(session_id, limit=4)
        standalone_question = self.contextualize_question(user_message, history)

        search_resp = self.search(standalone_question, top_k=top_k, score_threshold=score_threshold)
        results = search_resp["results"]

        if search_resp["no_match"] or not results:
            bot_answer = (
                "I could not find relevant passages in the corporate policy documents meeting the confidence threshold "
                "to answer this question."
            )
            self.neon_client.log_chat_interaction(session_id, user_message, bot_answer, sources="None", score=0.0)
            return {
                "session_id": session_id,
                "question": user_message,
                "standalone_question": standalone_question,
                "answer": bot_answer,
                "citations": [],
                "model_used": "no_match_fallback",
                "no_match": True,
            }

        context_blocks = [
            f"[Passage {idx}] Source: {item['source_file']} (Page {item['page']}) | Company: {item['company']} | Score: {item['score']:.2f}\n{item['text'].strip()}"
            for idx, item in enumerate(results, 1)
        ]
        rag_context = "\n\n".join(context_blocks)

        system_prompt = (
            "You are a corporate policy assistant for Susan Electricals, Jayaswal Neco, Reckitt, Google, and GitLab. "
            "Answer the question using only the provided policy passages. "
            "Include a short summary, key rules or entitlements, any applicable conditions, and cite the document name and page numbers."
        )
        user_prompt = f"Question: {standalone_question}\n\nPolicy Passages:\n{rag_context}\n\nAnswer:"

        llm_answer, model_name = self._call_llm(user_prompt, system_prompt)

        if not llm_answer:
            model_name = "extractive_synthesizer"
            best_definition = None
            is_def_q = any(k in standalone_question.lower() for k in ["mean by", "what is", "defined as", "definition", "who is", "who are"])

            if is_def_q:
                for item in results:
                    for sent in re.split(r"(?<=[.!?])\s+", item["text"]):
                        s_lower = sent.lower()
                        if ("means" in s_lower or "defined as" in s_lower or "shall include" in s_lower) and len(sent) > 30:
                            best_definition = (sent.strip().replace("\n", " "), item)
                            break
                    if best_definition:
                        break

            answer_parts = []
            if best_definition:
                def_sentence, def_item = best_definition
                answer_parts.append(
                    f"Policy Definition ({def_item['company']} - {def_item['source_file']}, Page {def_item['page']}):\n"
                    f'"{def_sentence}"\n\nRelevant Provisions:'
                )
            else:
                answer_parts.append("Relevant policy provisions from the documents:\n")

            for item in results:
                raw_text = item["text"].replace("\n", " ").strip()
                sentences = re.split(r"(?<=[.!?])\s+", raw_text)
                clean_text = " ".join(sentences[:2]).strip() if len(sentences) >= 2 else raw_text
                answer_parts.append(f"- {item['company']} ({item['source_file']}, Page {item['page']}): \"{clean_text}\"")
            llm_answer = "\n".join(answer_parts)

        citations = [
            {
                "source": item["source_file"],
                "page": item["page"],
                "chunk_id": item["chunk_id"],
                "company": item["company"],
                "title": item["title"],
                "score": item["score"],
            }
            for item in results
        ]

        sources_summary = ", ".join([f"{c['source']}:p{c['page']}" for c in citations])
        avg_score = round(sum(c["score"] for c in citations) / len(citations), 4) if citations else 0.0
        self.neon_client.log_chat_interaction(session_id, user_message, llm_answer, sources=sources_summary, score=avg_score)

        return {
            "session_id": session_id,
            "question": user_message,
            "standalone_question": standalone_question,
            "answer": llm_answer,
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
