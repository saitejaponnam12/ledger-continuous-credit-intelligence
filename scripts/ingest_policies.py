"""
LEDGER — Policy Document Ingestion Script
Chunks policy documents and embeds them into pgvector.

Pipeline:
  policy_documents table → chunk (512 tokens, 64 overlap)
  → sentence-transformers (all-MiniLM-L6-v2)
  → pgvector policy_chunks table

Run: python scripts/ingest_policies.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import AsyncSessionLocal
from app.models.models import PolicyChunk, PolicyDocument
from app.rag.retriever import embed_texts, get_embedding_model
from sqlalchemy import delete, select


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into overlapping chunks by character count.
    Tries to split on sentence boundaries when possible.
    """
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find sentence boundary
        boundary = text.rfind(". ", start, end)
        if boundary > start + chunk_size // 2:
            end = boundary + 1
        elif text.rfind("\n", start, end) > start + chunk_size // 2:
            end = text.rfind("\n", start, end)

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if len(c) > 20]


async def ingest_all() -> None:
    print("\n" + "=" * 60)
    print("LEDGER — Policy Document Ingestion (RAG)")
    print("=" * 60)

    # Load embedding model once
    print("\n[1/4] Loading sentence-transformers model...")
    model = get_embedding_model()
    print(f"  Model: all-MiniLM-L6-v2 | Dimensions: 384")

    async with AsyncSessionLocal() as session:
        # Fetch all policy documents
        print("\n[2/4] Fetching policy documents...")
        result = await session.execute(select(PolicyDocument))
        docs = result.scalars().all()

        if not docs:
            print("  No policy documents found. Run scripts/setup_db.py first.")
            return

        print(f"  Found {len(docs)} documents")

        # Delete existing chunks (re-ingest)
        print("\n[3/4] Re-ingesting chunks...")
        await session.execute(delete(PolicyChunk))
        await session.flush()

        total_chunks = 0
        for doc in docs:
            chunks = chunk_text(doc.content, chunk_size=600, overlap=80)
            texts = chunks

            # Batch embed
            embeddings = embed_texts(texts)

            for i, (chunk_text_val, embedding) in enumerate(zip(texts, embeddings)):
                chunk = PolicyChunk(
                    policy_document_id=doc.id,
                    chunk_text=chunk_text_val,
                    chunk_index=i,
                    embedding=embedding,
                )
                session.add(chunk)

            total_chunks += len(chunks)
            print(f"  {doc.title[:55]}... -> {len(chunks)} chunks")

        await session.commit()

        print(f"\n[4/4] Verifying retrieval...")
        # Quick sanity check — retrieve for a test query
        from app.rag.retriever import retrieve_relevant_chunks
        test_results = await retrieve_relevant_chunks(
            session,
            "What evidence is needed for NTC applicants?",
            top_k=3,
        )
        print(f"  Test query returned {len(test_results)} chunks")
        if test_results:
            print(f"  Top result: '{test_results[0]['title'][:50]}...' (similarity: {test_results[0]['similarity']:.3f})")

        print(f"\n[SUCCESS] Ingested {total_chunks} policy chunks across {len(docs)} documents.")
    print("  pgvector index ready for semantic search")


if __name__ == "__main__":
    asyncio.run(ingest_all())
