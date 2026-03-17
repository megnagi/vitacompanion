import asyncio
import os
import uuid
import json
from datetime import datetime, timezone, date, timedelta

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic import AsyncAnthropic

from db import get_db
from models.user import User, UserHealthProfile, UserPersonaConfig, UserSchedulerState, DailyLog
from services.twilio_service import send_whatsapp

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

PERSONA_PROMPTS = {
    "friend":    "You are a warm, supportive wellness companion.",
    "coach":     "You are a direct, data-driven wellness coach.",
    "commander": "You are an intense drill-sergeant coach — tough but never shameful.",
}


async def _load_user_context(user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    result = await db.execute(select(UserHealthProfile).where(UserHealthProfile.user_id == user_id))
    health_profile = result.scalar_one_or_none()

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == user_id))
    persona_config = result.scalar_one_or_none()

    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == date.today())
    )
    daily_log = result.scalar_one_or_none()

    return user, health_profile, persona_config, daily_log


async def _generate_nudge(system: str, user_prompt: str) -> str:
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    delays = [1, 2, 4]
    for attempt, delay in enumerate(delays, start=1):
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=100,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text.strip()
        except anthropic.InternalServerError as exc:
            if attempt == len(delays):
                raise
            print(f"[scheduler] Claude overloaded (attempt {attempt}), retrying in {delay}s: {exc}")
            await asyncio.sleep(delay)


def _build_log_summary(daily_log) -> str:
    if not daily_log:
        return "nothing logged yet today"
    parts = []
    if daily_log.weight_kg:
        parts.append(f"weight: {float(daily_log.weight_kg)}kg")
    if daily_log.calories_total:
        parts.append(f"kcal: {daily_log.calories_total}")
    if daily_log.protein_g:
        parts.append(f"protein: {float(daily_log.protein_g)}g")
    if daily_log.workout_completed:
        parts.append("workout: done")
    elif daily_log.workout_skipped:
        parts.append(f"workout: skipped")
    if daily_log.energy_level:
        parts.append(f"energy: {daily_log.energy_level}/5")
    if daily_log.sleep_hours:
        parts.append(f"sleep: {float(daily_log.sleep_hours)}h")
    return " | ".join(parts) if parts else "nothing logged yet today"


@router.post("/checkin/{user_id}", status_code=status.HTTP_200_OK)
async def send_checkin(user_id: str, db: AsyncSession = Depends(get_db)):
    uid = uuid.UUID(user_id)
    user, health_profile, persona_config, daily_log = await _load_user_context(uid, db)

    persona = persona_config.active_persona if persona_config else "friend"
    goal = health_profile.primary_goal.replace("_", " ") if health_profile else "general health"
    age = (date.today() - user.date_of_birth).days // 365
    log_summary = _build_log_summary(daily_log)

    system = (
        f"IMPORTANT: Reply in 1-2 sentences only. Be direct.\n"
        f"{PERSONA_PROMPTS[persona]}\n"
        f"User: {user.full_name.split()[0]}, {age}yo, goal: {goal}.\n"
        f"Reply in {user.language}."
    )
    user_prompt = (
        f"Send a morning check-in message. Today's log so far: {log_summary}. "
        f"Encourage them to log their day and stay on track."
    )

    nudge_text = await _generate_nudge(system, user_prompt)

    whatsapp_sent = False
    nudge_log_id = None
    whatsapp_error = None
    if user.phone_number:
        try:
            whatsapp_sent, nudge_log_id = await send_whatsapp(
                to_number=user.phone_number,
                message=nudge_text,
                db=db,
                user_id=user_id,
                nudge_type="checkin",
            )
        except Exception as exc:
            whatsapp_error = str(exc)
            print(f"[scheduler] checkin WhatsApp failed for {user_id}: {exc}")

    # Update scheduler state
    now = datetime.now(timezone.utc)
    result = await db.execute(select(UserSchedulerState).where(UserSchedulerState.user_id == uid))
    scheduler_state = result.scalar_one_or_none()
    if scheduler_state:
        scheduler_state.last_checkin_at = now
        scheduler_state.next_checkin_at = now + timedelta(days=1)
        scheduler_state.updated_at = now
        await db.commit()

    return {
        "user_id": user_id,
        "nudge_type": "checkin",
        "message": nudge_text,
        "whatsapp_sent": whatsapp_sent,
        "nudge_log_id": nudge_log_id,
        "has_phone": bool(user.phone_number),
        **({"whatsapp_error": whatsapp_error} if whatsapp_error else {}),
    }


@router.post("/nudge/{user_id}", status_code=status.HTTP_200_OK)
async def send_nudge(user_id: str, db: AsyncSession = Depends(get_db)):
    uid = uuid.UUID(user_id)
    user, health_profile, persona_config, daily_log = await _load_user_context(uid, db)

    persona = persona_config.active_persona if persona_config else "friend"
    goal = health_profile.primary_goal.replace("_", " ") if health_profile else "general health"
    age = (date.today() - user.date_of_birth).days // 365
    log_summary = _build_log_summary(daily_log)

    system = (
        f"IMPORTANT: Reply in 1-2 sentences only. Be direct.\n"
        f"{PERSONA_PROMPTS[persona]}\n"
        f"User: {user.full_name.split()[0]}, {age}yo, goal: {goal}.\n"
        f"Reply in {user.language}."
    )
    user_prompt = (
        f"Send a motivational nudge mid-day. Today's log so far: {log_summary}. "
        f"Focus on their goal ({goal}) and encourage them to keep going or start if they haven't yet."
    )

    nudge_text = await _generate_nudge(system, user_prompt)

    whatsapp_sent = False
    nudge_log_id = None
    whatsapp_error = None
    if user.phone_number:
        try:
            whatsapp_sent, nudge_log_id = await send_whatsapp(
                to_number=user.phone_number,
                message=nudge_text,
                db=db,
                user_id=user_id,
                nudge_type="motivation",
            )
        except Exception as exc:
            whatsapp_error = str(exc)
            print(f"[scheduler] nudge WhatsApp failed for {user_id}: {exc}")

    # Update scheduler state
    now = datetime.now(timezone.utc)
    result = await db.execute(select(UserSchedulerState).where(UserSchedulerState.user_id == uid))
    scheduler_state = result.scalar_one_or_none()
    if scheduler_state:
        scheduler_state.last_nudge_sent_at = now
        scheduler_state.updated_at = now
        await db.commit()

    return {
        "user_id": user_id,
        "nudge_type": "motivation",
        "message": nudge_text,
        "whatsapp_sent": whatsapp_sent,
        "nudge_log_id": nudge_log_id,
        "has_phone": bool(user.phone_number),
        **({"whatsapp_error": whatsapp_error} if whatsapp_error else {}),
    }
