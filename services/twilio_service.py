from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from twilio.rest import Client


def _get_twilio_client() -> Client:
    return Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
    )


async def send_whatsapp(
    to_number: str,
    message: str,
    db: AsyncSession,
    user_id: str,
    nudge_type: str,
) -> tuple[bool, str]:
    """
    Send a WhatsApp message via Twilio and record the attempt in nudge_log.

    Returns (success: bool, nudge_log_id: str).
    """
    now = datetime.now(timezone.utc)
    nudge_id = uuid.uuid4()
    to_wa = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    from_wa = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Insert row as pending
    await db.execute(
        text("""
            INSERT INTO nudge_log
                (id, user_id, channel, nudge_type, content, status, scheduled_at)
            VALUES
                (:id, :user_id, 'whatsapp', :nudge_type, :content, 'pending', :scheduled_at)
        """),
        {
            "id": nudge_id,
            "user_id": uuid.UUID(user_id),
            "nudge_type": nudge_type,
            "content": message,
            "scheduled_at": now,
        },
    )

    try:
        client = _get_twilio_client()

        def _send():
            return client.messages.create(
                from_=from_wa,
                body=message,
                to=to_wa,
            )

        twilio_msg = await asyncio.to_thread(_send)

        await db.execute(
            text("""
                UPDATE nudge_log
                SET status = 'sent', sent_at = :sent_at, twilio_sid = :twilio_sid
                WHERE id = :id
            """),
            {"id": nudge_id, "sent_at": now, "twilio_sid": twilio_msg.sid},
        )
        await db.commit()
        print(f"[twilio] sent {nudge_type} to {to_wa}  sid={twilio_msg.sid}")
        return True, str(nudge_id)

    except Exception as exc:
        await db.execute(
            text("""
                UPDATE nudge_log
                SET status = 'failed', error_detail = :error
                WHERE id = :id
            """),
            {"id": nudge_id, "error": str(exc)},
        )
        await db.commit()
        print(f"[twilio] FAILED {nudge_type} to {to_wa}: {exc}")
        return False, str(nudge_id)
