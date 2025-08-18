import os
import asyncio
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()

from app.db import connect_db, close_db, db  # type: ignore
from app.services.vector_store import get_store  # type: ignore

COLLECTION = "meetings"
BATCH = 200

async def fetch_embedding_docs() -> List[dict]:
    items: List[dict] = []
    cursor = db()[COLLECTION].find({
        "$or": [
            {"titleEmbedding": {"$type": "array"}},
            {"summaryEmbedding": {"$type": "array"}}
        ]
    }, projection={
        "titleEmbedding": 1,
        "summaryEmbedding": 1,
    })
    async for d in cursor:
        d["_id"] = str(d["_id"])  # stringify for vector ids
        items.append(d)
    return items

async def main():
    # VECTOR_BACKEND should be set to pinecone in .env
    backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
    if backend != "pinecone":
        print(f"[WARN] VECTOR_BACKEND is '{backend}'. Set VECTOR_BACKEND=pinecone to backfill Pinecone.")
    await connect_db()
    try:
        docs = await fetch_embedding_docs()
        if not docs:
            print("No documents with embeddings found. Nothing to backfill.")
            return
        # Determine dimension from first available embedding
        first_vec = None
        for d in docs:
            if isinstance(d.get("summaryEmbedding"), list) and d["summaryEmbedding"]:
                first_vec = d["summaryEmbedding"]
                break
            if isinstance(d.get("titleEmbedding"), list) and d["titleEmbedding"]:
                first_vec = d["titleEmbedding"]
                break
        if not first_vec:
            print("No embedding vectors found in docs.")
            return
        dim = len(first_vec)
        store = get_store(dim)
        # Upsert in batches per scope
        title_batch: List[Tuple[str, List[float]]] = []
        summary_batch: List[Tuple[str, List[float]]] = []
        total_title = total_summary = 0
        for d in docs:
            mid = d["_id"]
            t = d.get("titleEmbedding")
            s = d.get("summaryEmbedding")
            if isinstance(t, list) and t:
                title_batch.append((mid, t))
            if isinstance(s, list) and s:
                summary_batch.append((mid, s))
            # Flush in batches
            if len(title_batch) >= BATCH:
                store.bulk_load("title", title_batch)
                total_title += len(title_batch)
                title_batch.clear()
            if len(summary_batch) >= BATCH:
                store.bulk_load("summary", summary_batch)
                total_summary += len(summary_batch)
                summary_batch.clear()
        # Flush remaining
        if title_batch:
            store.bulk_load("title", title_batch)
            total_title += len(title_batch)
        if summary_batch:
            store.bulk_load("summary", summary_batch)
            total_summary += len(summary_batch)
        print(f"Backfill complete. Upserted {total_title} title vectors and {total_summary} summary vectors to Pinecone.")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
