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

        if "posh" in lower_q or "harassment" in lower_q:
            queries.append("Prevention of Sexual Harassment workplace policy internal complaints committee procedure redressal")
        elif any(w in lower_q for w in ["leave", "maternity", "parental", "paternity"]):
            queries.append("parental leave policy maternity benefit entitlement primary secondary caregiver adoption")
        elif "csr" in lower_q or "social responsibility" in lower_q:
            queries.append("corporate social responsibility policy annual action plan committee allocation")
        elif any(w in lower_q for w in ["bribery", "gift", "corruption"]):
            queries.append("anti-corruption anti-bribery code of conduct gifts hospitality entertaining")
        elif "whistleblower" in lower_q or "vigil" in lower_q:
            queries.append("vigil mechanism whistleblower policy protected disclosure investigation audit committee")
        elif "upsi" in lower_q or "insider" in lower_q:
            queries.append("unpublished price sensitive information fair disclosure code of practices insider trading")
        elif any(w in lower_q for w in ["human rights", "labour", "labor", "child labour", "forced labour"]):
            queries.append("human rights policy labour standards fair treatment non-discrimination International Labour Organisation")
        elif any(w in lower_q for w in ["supplier", "vendor", "supply chain", "representative"]):
            queries.append("supply chain policy supplier representative code of conduct vendor standards ESG business ethics")
        elif any(w in lower_q for w in ["expense", "travel", "reimbursement", "per diem"]):
            queries.append("expense policy travel meals accommodation reimbursement allowable expenses GitLab")

        return queries

    def calibrate_score(self, raw_score: float) -> float:
        if raw_score <= 0.25:
            return 0.0
        calibrated = (raw_score - 0.28) / (0.68 - 0.28)
        return round(min(1.0, max(0.0, calibrated)), 4)

    def search(self, question: str, top_k: int = 5, score_threshold: float = 0.75) -> dict:
        all_queries = self.expand_queries(question)
        aggregated_matches = {}

        for q_text in all_queries:
            query_res = self.collection.query(
                query_texts=[q_text],
                n_results=top_k * 3,
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
                raw_similarity = round(max(0.0, 1.0 - dist), 4) if dist is not None else 0.0
                calibrated_confidence = self.calibrate_score(raw_similarity)
                rrf_score = 1.0 / (60 + rank)

                if cid not in aggregated_matches:
                    aggregated_matches[cid] = {
                        "text": doc_text,
                        "source_file": meta.get("source", ""),
                        "page": int(meta.get("page", 1)),
                        "score": calibrated_confidence,
                        "raw_score": raw_similarity,
                        "chunk_id": cid,
                        "title": meta.get("title", ""),
                        "company": meta.get("company", ""),
                        "rrf": rrf_score,
                    }
                else:
                    aggregated_matches[cid]["rrf"] += rrf_score
                    if calibrated_confidence > aggregated_matches[cid]["score"]:
                        aggregated_matches[cid]["score"] = calibrated_confidence
                        aggregated_matches[cid]["raw_score"] = raw_similarity

        sorted_candidates = sorted(
            aggregated_matches.values(),
            key=lambda x: (x["score"] >= score_threshold, x["score"], x["rrf"]),
            reverse=True,
        )

        seen_snippets = set()
        filtered_results = []
        for c in sorted_candidates:
            if c["score"] < score_threshold:
                continue
            norm_snip = re.sub(r"\s+", " ", c["text"][:100].strip().lower())
            if norm_snip in seen_snippets:
                continue
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
