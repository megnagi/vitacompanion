from dotenv import load_dotenv
load_dotenv()

import json
import uuid
import os
from datetime import datetime, timezone, date
from typing import Optional, AsyncGenerator
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from anthropic import AsyncAnthropic

from models.user import User, UserHealthProfile, UserPersonaConfig, DailyLog
from models.conversation import Conversation, Message
from services.rag_service import retrieve_similar_documents


# ─── Request / Response Schemas ─────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty or whitespace")
        return v


# ─── Persona system prompts (1 sentence each) ────────────────────

PERSONA_PROMPTS = {
    "friend":    "You are a warm, supportive wellness companion who speaks like a caring friend — encouraging, non-judgmental, and celebratory of small wins.",
    "coach":     "You are a direct, data-driven wellness coach who gives precise, actionable feedback grounded in the user's numbers and goals.",
    "commander": "You are an intense drill-sergeant coach who uses punchy, no-excuses language — tough but never shameful about medical issues or pain.",
}

SAFETY_OVERRIDE = "If the user mentions pain, injury, or emotional distress — switch to a caring tone immediately, regardless of persona."

DOMAIN_GUIDANCE = "Apply reference knowledge to your response: nutrition questions → dietary guidelines; training questions → exercise/HR-zone guidelines; safety concerns → safety info first."


# ─── Context assembly ────────────────────────────────────────────

def build_system_prompt(
        user: User,
        health_profile: UserHealthProfile,
        persona_config: Optional[UserPersonaConfig],
        daily_log: Optional[DailyLog],
        rag_docs: list[dict],
) -> str:
    today_str = date.today().strftime("%A, %B %d, %Y")
    age = (date.today() - user.date_of_birth).days // 365 if user.date_of_birth else None
    persona = persona_config.active_persona if persona_config else "friend"

    log_parts = []
    if daily_log:
        if daily_log.weight_kg:
            log_parts.append(f"weight: {float(daily_log.weight_kg)}kg")
        if daily_log.calories_total:
            log_parts.append(f"kcal: {daily_log.calories_total}")
        if daily_log.protein_g:
            log_parts.append(f"protein: {float(daily_log.protein_g)}g")
        if daily_log.workout_completed:
            log_parts.append("workout: done")
        elif daily_log.workout_skipped:
            log_parts.append(f"workout: skipped ({daily_log.skip_reason or '—'})")
        if daily_log.energy_level:
            log_parts.append(f"energy: {daily_log.energy_level}/5")
        if daily_log.mood_score:
            log_parts.append(f"mood: {daily_log.mood_score}/5")
        if daily_log.sleep_hours:
            log_parts.append(f"sleep: {float(daily_log.sleep_hours)}h")
        if daily_log.pain_reported:
            log_parts.append(f"⚠ PAIN: {daily_log.pain_detail or 'unspecified'}")
    log_summary = " | ".join(log_parts) if log_parts else "nothing logged yet"

    rag_section = ""
    if rag_docs:
        snippets = []
        for doc in rag_docs:
            body = doc["content"][:300].rstrip()
            snippets.append(f"[{doc['title']}] {body}…")
        rag_section = "\nREF:\n" + "\n".join(snippets)

    return (
        f"IMPORTANT: Reply in 2-3 sentences maximum. Be direct. No lists unless explicitly asked.\n"
        f"You are VitaCompanion, an AI wellness coach for adults 50+. "
        f"Today: {today_str}.\n"
        f"User: {user.full_name.split()[0]}, {f'{age}yo ' if age else ''}{user.sex or 'unknown sex'}, DOB: {user.date_of_birth or 'unknown'}, goal: {health_profile.primary_goal.replace('_', ' ')}, lang: {user.language}.\n"
        f"Today's log: {log_summary}.\n"
        f"Persona: {PERSONA_PROMPTS[persona]}\n"
        f"Safety: {SAFETY_OVERRIDE}\n"
        f"Domains: {DOMAIN_GUIDANCE}"
        f"{rag_section}\n"
        f"Reply in {user.language}."
    )


# ─── Shared context loader ────────────────────────────────────────

async def _load_context(data: ChatRequest, db: AsyncSession):
    """Load all DB state needed to handle a chat message."""
    user_id = uuid.UUID(data.user_id)
    now = datetime.now(timezone.utc)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {data.user_id} not found")

    result = await db.execute(select(UserHealthProfile).where(UserHealthProfile.user_id == user_id))
    health_profile = result.scalar_one_or_none()
    if not health_profile:
        raise ValueError(f"Health profile not found for user {data.user_id}")

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == user_id))
    persona_config = result.scalar_one_or_none()
    if not persona_config:
        raise ValueError(f"Persona config not found for user {data.user_id}")

    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == date.today())
    )
    daily_log = result.scalar_one_or_none()

    # Conversation
    conversation = None
    if data.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(data.conversation_id),
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            bot_type="orchestrator",
            started_at=now,
            last_message_at=now,
            is_active=True,
        )
        db.add(conversation)
        await db.flush()

    # Recent messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(desc(Message.created_at))
        .limit(6)
    )
    recent_messages = list(reversed(result.scalars().all()))

    # RAG
    rag_docs = await retrieve_similar_documents(
        db=db, query=data.message, top_k=3, user_id=str(user_id)
    )

    system_prompt = build_system_prompt(user, health_profile, persona_config, daily_log, rag_docs)

    claude_messages = [
        {"role": m.role, "content": m.content}
        for m in recent_messages
        if m.role in ("user", "assistant")
    ]
    claude_messages.append({"role": "user", "content": data.message})

    persona = persona_config.active_persona if persona_config else "friend"

    return user_id, conversation, system_prompt, claude_messages, persona, now


# ─── Streaming chat ───────────────────────────────────────────────

async def stream_chat(
        data: ChatRequest,
        db: AsyncSession,
) -> AsyncGenerator[str, None]:
    user_id, conversation, system_prompt, claude_messages, persona, now = \
        await _load_context(data, db)

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    full_text = ""
    input_tokens = 0
    output_tokens = 0

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=200,
            system=system_prompt,
            messages=claude_messages,
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield f"data: {json.dumps({'chunk': text})}\n\n"

            final = await stream.get_final_message()
            input_tokens = final.usage.input_tokens
            output_tokens = final.usage.output_tokens
    except Exception:
        fallback = "I'm having trouble connecting right now. Please try again in a moment."
        full_text = fallback
        yield f"data: {json.dumps({'chunk': fallback})}\n\n"

    # Save to DB after stream completes
    user_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=data.message,
        safety_flag_raised=False,
        created_at=now,
    )
    db.add(user_msg)

    assistant_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content=full_text,
        bot_source="orchestrator",
        persona_applied=persona,
        safety_flag_raised=False,
        raw_bot_response={
            "model": "claude-sonnet-4-5",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        },
        token_count=input_tokens + output_tokens,
        created_at=now,
    )
    db.add(assistant_msg)

    conversation.last_message_at = now
    await db.commit()

    yield f"data: {json.dumps({'done': True, 'conversation_id': str(conversation.id), 'message_id': str(assistant_msg.id)})}\n\n"
