"""
chunker.py
==========
Text Chunking & Splitting Strategies (Day 3 - Session 2)

Learning Goals Covered:
1. Fixed vs. Recursive vs. Semantic chunking
2. Chunk size and overlap trade-offs (300 tokens vs. 800 tokens)
3. Preserving and enriching metadata across chunks (source, page, chunk_id, token_count)
"""

from typing import List, Dict, Any
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pdf_loader import Document

# Tokenizer for accurate token accounting
TOKENIZER = tiktoken.get_encoding("cl100k_base")


class ChunkedDocument:
    """
    Enriched chunk representation carrying original document metadata
    and chunk-specific structural telemetry.
    """
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata

    @property
    def token_count(self) -> int:
        return self.metadata.get("token_count", len(TOKENIZER.encode(self.page_content)))

    def __repr__(self) -> str:
        cid = self.metadata.get("chunk_id", "c?")
        src = self.metadata.get("source", "?")
        pg = self.metadata.get("page", "?")
        tokens = self.metadata.get("token_count", "?")
        return f"<Chunk [{cid}] {src}:P{pg} ({tokens} tokens)>"


def build_recursive_splitters():
    """
    Builds the two target token-aware recursive text splitters:
    1. Small Chunks: 300 tokens, 50 token overlap (high retrieval precision)
    2. Large Chunks: 800 tokens, 100 token overlap (broad contextual continuity)
    """
    splitter_300 = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    splitter_800 = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return splitter_300, splitter_800


def chunk_documents(
    documents: List[Document],
    chunk_size_tokens: int = 300,
    chunk_overlap_tokens: int = 50,
) -> List[ChunkedDocument]:
    """
    Splits a list of page-level Documents into token-bounded chunks while
    preserving and enriching parent metadata.

    Args:
        documents: List of input Document objects.
        chunk_size_tokens: Target maximum tokens per chunk (300 or 800).
        chunk_overlap_tokens: Overlap in tokens between consecutive chunks.

    Returns:
        List of ChunkedDocument objects with unique IDs and metadata.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size_tokens,
        chunk_overlap=chunk_overlap_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunked_results: List[ChunkedDocument] = []
    global_chunk_idx = 0

    for doc in documents:
        # Split individual page text
        sub_texts = splitter.split_text(doc.page_content)

        for sub_idx, chunk_text in enumerate(sub_texts):
            clean_text = chunk_text.strip()
            if not clean_text:
                continue

            token_count = len(TOKENIZER.encode(clean_text))
            source_stem = doc.metadata.get("source", "doc").replace(".pdf", "")
            page_num = doc.metadata.get("page", 1)

            # Metadata inheritance + chunk enrichment
            chunk_metadata = {
                **doc.metadata,
                "chunk_id": f"{source_stem}_p{page_num}_c{sub_idx}",
                "chunk_index": global_chunk_idx,
                "chunk_size_setting": f"{chunk_size_tokens}_tokens",
                "overlap_setting": f"{chunk_overlap_tokens}_tokens",
                "token_count": token_count,
                "char_count": len(clean_text),
            }

            chunked_results.append(
                ChunkedDocument(page_content=clean_text, metadata=chunk_metadata)
            )
            global_chunk_idx += 1

    return chunked_results


# ---------------------------------------------------------------------------
# EDUCATIONAL THEORY: FIXED vs RECURSIVE vs SEMANTIC CHUNKING
# ---------------------------------------------------------------------------
CHUNKING_COMPARISON_NOTES = """
=============================================================================
CHUNKING STRATEGIES COMPARISON
=============================================================================
1. Fixed-Size Chunking:
   - Slices text every N characters or words indiscriminately.
   - Flaw: Cuts words in half, severs sentences mid-thought, breaks tables.
   - When to use: Raw binary dumps or fixed-width telemetry data.

2. Recursive Character Chunking (LangChain RecursiveCharacterTextSplitter):
   - Hierarchically attempts splits in order: ["\\n\\n", "\\n", " ", ""].
   - First tries splitting on paragraph boundaries (preserving paragraphs).
   - If a paragraph exceeds chunk_size, splits on newline (preserving lines).
   - If still too long, splits on sentences or spaces.
   - Result: Maximally preserves syntactic and semantic coherence.

3. Semantic Chunking:
   - Computes embedding vectors for every individual sentence.
   - Measures cosine distance between sentence i and sentence i+1.
   - When cosine distance exceeds a threshold (e.g. 95th percentile shift),
     a new chunk boundary is created (detects topic shifts).
   - Flaw: Computationally heavy (requires N embedding API calls before chunking).

=============================================================================
CHUNK SIZE & OVERLAP TRADE-OFFS (300 vs 800 Tokens)
=============================================================================
- 300-Token Chunks (Small):
  * Pros:
    - High retrieval precision (embedding represents a single focused concept).
    - Minimizes context window bloat and reduces LLM inference cost.
  * Cons:
    - Context fragmentation: Multi-step rules spanning multiple paragraphs
      can get sliced across chunk boundaries.
    - Loss of antecedents (e.g., pronouns "this", "it" separated from subject).

- 800-Token Chunks (Large):
  * Pros:
    - Excellent context retention (holds entire sub-sections, rules + exceptions).
    - Fewer total chunks to index in vector database.
  * Cons:
    - "Vector Dilution": Embedding vector averages 4-5 different sub-topics,
      reducing semantic distinctiveness for niche factual lookups.
    - Wastes LLM context window with extraneous irrelevant sentences.

- Overlap (50-100 Tokens):
  * Essential glue: Prevents sentences from being clipped in half.
  * Ensures critical named entities or rules appearing at the boundary
    are represented in both adjacent chunks.
=============================================================================
"""


if __name__ == "__main__":
    from pathlib import Path
    from pdf_loader import load_all_pdfs

    docs_dir = Path(__file__).parent / "docs"
    docs = load_all_pdfs(docs_dir)

    chunks_300 = chunk_documents(docs, chunk_size_tokens=300, chunk_overlap_tokens=50)
    chunks_800 = chunk_documents(docs, chunk_size_tokens=800, chunk_overlap_tokens=100)

    print(f"\nIngested {len(docs)} PDF pages.")
    print(f"300-token chunker produced: {len(chunks_300)} chunks.")
    print(f"800-token chunker produced: {len(chunks_800)} chunks.")
    print("\nSample 300-token chunk:")
    print(chunks_300[0])
    print("Content preview:", chunks_300[0].page_content[:150], "...")
    print("\nSample 800-token chunk:")
    print(chunks_800[0])
    print("Content preview:", chunks_800[0].page_content[:150], "...")
