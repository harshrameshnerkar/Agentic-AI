import os
import sys
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

from extraction import extract_all, chunk_pages
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


def get_paths():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(curr_dir, "data", "documents")
    meta_path = os.path.join(curr_dir, "data", "documents_metadata.json")
    db_path = os.path.join(curr_dir, "db", "chroma_db")
    return os.path.abspath(docs_path), os.path.abspath(meta_path), os.path.abspath(db_path)


def get_embedding_function():
    return embedding_functions.DefaultEmbeddingFunction(), "all-MiniLM-L6-v2"


def sync_to_neon(chunks, embedding_model_name: str):
    try:
        client = NeonDBClient()
        db_info = client.test_connection()
        print(f"Connected to Neon DB: {db_info.get('database')} ({db_info.get('user')})")

        formatted = [
            {
                "chunk_id": ch.chunk_id,
                "text": ch.text,
                "source": ch.metadata["source"],
                "page": ch.metadata["page"],
                "score": None,
            }
            for ch in chunks
        ]

        stats = client.sync_chunks(formatted, embedding_model_name=embedding_model_name, batch_size=100)
        print(f"Neon sync stats: {stats}")
        return True
    except Exception as e:
        print(f"Neon sync failed: {e}")
        return False


def update_vector_store(chunks, embedding_func, db_path: str, batch_size: int = 100):
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(
        name="rag_documents",
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )

    existing_map = {}
    try:
        data = collection.get(include=["documents", "metadatas"])
        for cid, doc, meta in zip(data.get("ids", []), data.get("documents", []), data.get("metadatas", [])):
            existing_map[cid] = (doc, meta or {})
    except Exception:
        pass

    existing = set(existing_map.keys())
    valid_ids = {c.chunk_id for c in chunks}
    stale_ids = list(existing - valid_ids)
    if stale_ids:
        print(f"Removing {len(stale_ids)} stale chunks from ChromaDB...")
        for i in range(0, len(stale_ids), batch_size):
            collection.delete(ids=stale_ids[i : i + batch_size])
        for sid in stale_ids:
            existing_map.pop(sid, None)

    new_chunks = [
        c
        for c in chunks
        if c.chunk_id not in existing_map
        or existing_map[c.chunk_id][0] != c.text
        or existing_map[c.chunk_id][1].get("source") != c.metadata.get("source")
    ]
    if not new_chunks:
        print(f"ChromaDB already up to date ({collection.count()} chunks).")
        return collection

    print(f"Indexing {len(new_chunks)} new chunks into ChromaDB...")
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i : i + batch_size]
        collection.upsert(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )

    print(f"Total indexed chunks in ChromaDB: {collection.count()}")
    return collection


def main():
    docs_path, meta_path, db_path = get_paths()

    print("Extracting documents...")
    pages, _ = extract_all(docs_dir=docs_path, meta_path=meta_path, enable_ocr=True, verbose=False, write_report=True)
    print(f"Extracted {len(pages)} pages from 50 documents.")

    print("Chunking pages (size=500, overlap=75)...")
    chunks = chunk_pages(pages, chunk_size=500, chunk_overlap=75)
    print(f"Created {len(chunks)} chunks.")

    embedding_func, model_name = get_embedding_function()
    sync_to_neon(chunks, embedding_model_name=model_name)
    update_vector_store(chunks, embedding_func, db_path)
    print(f"Ingestion finished ({len(chunks)} chunks active).")


if __name__ == "__main__":
    main()
