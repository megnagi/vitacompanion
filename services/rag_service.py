from dotenv import load_dotenv
load_dotenv()

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
import os

from sqlalchemy import text
from openai import AsyncOpenAI

_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-ada-002"


# ─── Embedding ───────────────────────────────────────────────────

async def embed_text(text_input: str) -> list[float]:
    response = await _openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_input,
    )
    return response.data[0].embedding


# ─── Insert ──────────────────────────────────────────────────────

async def insert_document(
    db: AsyncSession,
    title: str,
    content: str,
    category: str,
    user_id: Optional[str] = None,
) -> str:
    """Embed content and insert a document into rag_documents. Returns the new document id."""
    embedding = await embed_text(content)
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    doc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    import json
    metadata = json.dumps({"title": title})

    await db.execute(
        text("""
            INSERT INTO rag_documents (id, user_id, doc_type, source_id, content, embedding, metadata, created_at)
            VALUES (:id, :user_id, :doc_type, NULL, :content, CAST(:embedding AS vector), CAST(:metadata AS jsonb), :created_at)
        """),
        {
            "id": doc_id,
            "user_id": uuid.UUID(user_id) if user_id else None,
            "doc_type": category,
            "content": content,
            "embedding": embedding_str,
            "metadata": metadata,
            "created_at": now,
        },
    )
    return str(doc_id)


# ─── Retrieve ────────────────────────────────────────────────────

async def retrieve_similar_documents(
    db: AsyncSession,
    query: str,
    top_k: int = 3,
    user_id: Optional[str] = None,
    category: Optional[str] = None,
) -> list[dict]:
    """
    Return top_k documents ordered by cosine distance (ascending) to the query.

    Scope rules:
    - When user_id is provided: returns global docs (user_id IS NULL) AND
      that user's private docs.
    - When user_id is None: returns only global docs.
    - When category is provided: further narrows results to that category.
    """
    try:
        embedding = await embed_text(query)
    except Exception as exc:
        print(f"[rag] embed_text failed, skipping RAG context: {exc}")
        return []
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

    filters: list[str] = []
    params: dict = {
        "embedding": embedding_str,
        "top_k": top_k,
    }

    if user_id:
        filters.append("(user_id = :user_id OR user_id IS NULL)")
        params["user_id"] = uuid.UUID(user_id)
    else:
        filters.append("user_id IS NULL")

    if category:
        filters.append("doc_type = :doc_type")
        params["doc_type"] = category

    where_clause = "WHERE " + " AND ".join(filters)

    result = await db.execute(
        text(f"""
            SELECT id, doc_type, content, metadata, created_at,
                   embedding <=> CAST(:embedding AS vector) AS distance
            FROM rag_documents
            {where_clause}
            ORDER BY distance ASC
            LIMIT :top_k
        """),
        params,
    )

    rows = result.fetchall()
    return [
        {
            "id": str(row.id),
            "title": (row.metadata or {}).get("title", ""),
            "content": row.content,
            "category": row.doc_type,
            "distance": float(row.distance),
        }
        for row in rows
    ]
