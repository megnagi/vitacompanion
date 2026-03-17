#!/usr/bin/env python3
"""
scheduler_worker.py — Fire check-ins and nudges for all due users.

Use this when pg_net is unavailable (Option B in pg_cron_setup.sql).
The worker polls the nudge_queue table and calls the FastAPI scheduler
endpoints for each pending row.

Schedule via your hosting platform's cron feature, e.g.:
  Railway / Render cron job: python scheduler_worker.py
  OS cron (every minute):    * * * * * cd /app && python scheduler_worker.py

Or trigger directly for testing:
  python scheduler_worker.py
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
API_URL = os.getenv("SCHEDULER_API_URL", "http://localhost:8000")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def process_queue() -> None:
    async with AsyncSessionLocal() as db:
        # Fetch all unprocessed rows, oldest first
        result = await db.execute(
            text(
                "SELECT id, user_id, nudge_type FROM nudge_queue "
                "WHERE processed_at IS NULL "
                "ORDER BY queued_at ASC "
                "FOR UPDATE SKIP LOCKED"
            )
        )
        rows = result.fetchall()

        if not rows:
            print("[scheduler_worker] No pending jobs.")
            return

        async with httpx.AsyncClient(timeout=30) as client:
            for row_id, user_id, nudge_type in rows:
                url = f"{API_URL}/scheduler/{nudge_type}/{user_id}"
                try:
                    resp = await client.post(url)
                    resp.raise_for_status()
                    print(f"[scheduler_worker] {nudge_type} → user {user_id}: OK ({resp.status_code})")
                except httpx.HTTPStatusError as e:
                    print(f"[scheduler_worker] {nudge_type} → user {user_id}: HTTP {e.response.status_code}")
                except Exception as e:
                    print(f"[scheduler_worker] {nudge_type} → user {user_id}: ERROR {e}")

                # Mark processed regardless of success — avoid infinite retries
                await db.execute(
                    text("UPDATE nudge_queue SET processed_at = :now WHERE id = :id"),
                    {"now": datetime.now(timezone.utc), "id": str(row_id)},
                )

        await db.commit()
        print(f"[scheduler_worker] Processed {len(rows)} job(s).")


if __name__ == "__main__":
    asyncio.run(process_queue())
