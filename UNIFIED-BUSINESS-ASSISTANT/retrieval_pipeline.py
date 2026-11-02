import os
import sys
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(parent_env):
    load_dotenv(parent_env)

_CACHED_EF = None
_CACHED_MODEL_NAME = None
_CACHED_COLLECTION = None


def get_embedding_function():
    global _CACHED_EF, _CACHED_MODEL_NAME
    if _CACHED_EF is None:
        _CACHED_EF = embedding_functions.DefaultEmbeddingFunction()
        _CACHED_MODEL_NAME = "all-MiniLM-L6-v2"
    return _CACHED_EF, _CACHED_MODEL_NAME


def get_vector_store():
    global _CACHED_COLLECTION, _CACHED_MODEL_NAME
    if _CACHED_COLLECTION is not None:
        return _CACHED_COLLECTION, _CACHED_MODEL_NAME

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "db", "chroma_db")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"ChromaDB store not found at '{db_path}'. Run ingestion_pipeline.py first.")

    embedding_func, model_name = get_embedding_function()
    client = chromadb.PersistentClient(path=db_path)
    _CACHED_COLLECTION = client.get_collection(name="rag_documents", embedding_function=embedding_func)
    return _CACHED_COLLECTION, model_name


def retrieve(question: str, top_k: int = 5, score_threshold: float = 0.4):
    collection, model_name = get_vector_store()
    res = collection.query(
        query_texts=[question],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0] or []
    metas = (res.get("metadatas") or [[]])[0] or []
    dists = (res.get("distances") or [[]])[0] or []

    results = []
    for doc_text, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        similarity = round(max(0.0, 1.0 - dist), 4) if dist is not None else 0.0
        if similarity >= score_threshold:
            results.append(
                {
                    "text": doc_text or "",
                    "source_file": meta.get("source", ""),
                    "page": int(meta.get("page", 1)),
                    "score": similarity,
                    "chunk_id": meta.get("chunk_id", ""),
                    "title": meta.get("title", ""),
                    "company": meta.get("company", ""),
                }
            )

    return {
        "results": results,
        "no_match": len(results) == 0,
        "embedding_model": model_name,
    }


def print_retrieval_output(question: str, response: dict):
    print(f"\nQuery: {question}")
    print(f"Model: {response['embedding_model']} | Matches: {len(response['results'])} | No Match: {response['no_match']}")

    if response["no_match"]:
        print("No chunks met the relevance threshold.\n")
        return

    for idx, item in enumerate(response["results"], 1):
        print(f"\n[{idx}] Score: {item['score']:.4f} | {item['source_file']} (p. {item['page']}) | {item['chunk_id']}")
        print(f"    Company: {item['company']} | Title: {item['title']}")
        snippet = item["text"].strip().replace("\n", " ")
        print(f"    Text: {snippet[:280]}...")


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        resp = retrieve(question, top_k=5, score_threshold=0.35)
        print_retrieval_output(question, resp)
        return

    sample_queries = [
        "What is the procedure for reporting sexual harassment under POSH?",
        "What are the maternity and parental leave entitlements?",
        "What are the CSR committee guidelines and project allocations?",
        "What is the policy regarding gifts, hospitality, and anti-bribery?",
        "What are the whistleblower protection and vigil mechanism rules?",
    ]

    for q in sample_queries:
        resp = retrieve(q, top_k=3, score_threshold=0.35)
        print_retrieval_output(q, resp)


if __name__ == "__main__":
    main()
