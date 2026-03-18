import os
import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from anthropic import AsyncAnthropic

from models.user import User, UserHealthProfile, UserPersonaConfig, DailyLog
from models.log import MealLog, WorkoutLog


PERSONA_PROMPTS = {
    "friend":    "You are a warm, supportive wellness companion.",
    "coach":     "You are a direct, data-driven wellness coach.",
    "commander": "You are an intense drill-sergeant coach — tough but never shameful.",
}


# ─── Aggregation helpers ─────────────────────────────────────────

def _avg(values: list) -> Optional[float]:
    floats = [float(v) for v in values if v is not None]
    return round(sum(floats) / len(floats), 1) if floats else None


def _trend(current: Optional[float], previous: Optional[float]) -> str:
    if current is None or previous is None:
        return "insufficient_data"
    diff = current - previous
    if abs(diff) < 0.05:
        return "same"
    return "up" if diff > 0 else "down"


async def _aggregate_period(
    user_id: uuid.UUID,
    start: date,
    end: date,
    db: AsyncSession,
) -> dict:
    """Return aggregated stats for a date range [start, end)."""
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start,
            DailyLog.log_date < end,
        )
    )
    logs = result.scalars().all()

    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.log_date >= start,
            WorkoutLog.log_date < end,
        )
    )
    workouts = result.scalars().all()

    weights = [dl.weight_kg for dl in logs if dl.weight_kg is not None]
    calories = [dl.calories_total for dl in logs if dl.calories_total is not None]
    proteins = [dl.protein_g for dl in logs if dl.protein_g is not None]
    sleeps = [dl.sleep_hours for dl in logs if dl.sleep_hours is not None]
    moods = [dl.mood_score for dl in logs if dl.mood_score is not None]
    energies = [dl.energy_level for dl in logs if dl.energy_level is not None]

    workouts_completed = sum(1 for w in workouts if True)  # count all logged sessions
    has_data = bool(logs or workouts)

    return {
        "has_data": has_data,
        "weight_start_kg": float(weights[0]) if weights else None,
        "weight_end_kg": float(weights[-1]) if weights else None,
        "weight_delta_kg": round(float(weights[-1]) - float(weights[0]), 1) if len(weights) >= 2 else None,
        "avg_daily_calories": int(round(_avg(calories))) if _avg(calories) else None,
        "avg_protein_g": _avg(proteins),
        "avg_sleep_hours": _avg(sleeps),
        "avg_mood": _avg(moods),
        "avg_energy": _avg(energies),
        "workouts_completed": workouts_completed,
    }


async def _write_narrative(
    stats: dict,
    prev_stats: dict,
    user_name: str,
    goal: str,
    persona: str,
    language: str,
    period_label: str,
) -> str:
    if not stats["has_data"]:
        return (
            f"No data logged this {period_label} yet. "
            f"Start logging your meals, workouts, and daily check-ins to get your first report!"
        )

    cal_trend = _trend(stats["avg_daily_calories"], prev_stats["avg_daily_calories"])
    weight_trend = _trend(stats["weight_end_kg"], prev_stats["weight_end_kg"])
    sleep_trend = _trend(stats["avg_sleep_hours"], prev_stats["avg_sleep_hours"])

    context = (
        f"User: {user_name}, goal: {goal.replace('_', ' ')}. "
        f"This {period_label}: "
        f"avg calories {stats['avg_daily_calories'] or '—'} kcal (trend: {cal_trend}), "
        f"avg sleep {stats['avg_sleep_hours'] or '—'}h (trend: {sleep_trend}), "
        f"avg mood {stats['avg_mood'] or '—'}/5, "
        f"weight change {stats['weight_delta_kg'] or '—'} kg (trend: {weight_trend}), "
        f"workouts completed: {stats['workouts_completed']}."
    )

    system = (
        f"IMPORTANT: Plain text only — no markdown, no headers, no bold. "
        f"Complete your response within 3 sentences. Be specific and data-driven.\n"
        f"{PERSONA_PROMPTS[persona]}\n"
        f"Reply in {language}."
    )
    user_prompt = (
        f"Write a {period_label} wellness report narrative for this user. "
        f"Reference specific numbers. Highlight one win and one area to improve.\n{context}"
    )

    client = AsyncAnthropic(api_key=(os.getenv("ANTHROPIC_API_KEY") or "").strip())
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


async def _save_report(
    user_id: uuid.UUID,
    period: str,
    period_start: date,
    period_end: date,
    stats: dict,
    narrative: str,
    persona: str,
    db: AsyncSession,
) -> dict:
    from sqlalchemy import text

    report_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    raw = {
        "stats": stats,
        "narrative": narrative,
        "generated_at": now.isoformat(),
    }

    import json

    await db.execute(
        text("""
            INSERT INTO reports (
                id, user_id, period, period_start, period_end,
                avg_daily_calories, avg_protein_g,
                weight_start_kg, weight_end_kg, weight_delta_kg,
                workouts_completed,
                avg_energy, avg_mood, avg_sleep_hours,
                narrative_summary, raw_report_json,
                generated_at, persona_at_generation
            ) VALUES (
                :id, :user_id, :period, :period_start, :period_end,
                :avg_daily_calories, :avg_protein_g,
                :weight_start_kg, :weight_end_kg, :weight_delta_kg,
                :workouts_completed,
                :avg_energy, :avg_mood, :avg_sleep_hours,
                :narrative_summary, CAST(:raw_report_json AS jsonb),
                :generated_at, :persona_at_generation
            )
        """),
        {
            "id": report_id,
            "user_id": user_id,
            "period": period,
            "period_start": period_start,
            "period_end": period_end,
            "avg_daily_calories": stats["avg_daily_calories"],
            "avg_protein_g": stats["avg_protein_g"],
            "weight_start_kg": stats["weight_start_kg"],
            "weight_end_kg": stats["weight_end_kg"],
            "weight_delta_kg": stats["weight_delta_kg"],
            "workouts_completed": stats["workouts_completed"],
            "avg_energy": stats["avg_energy"],
            "avg_mood": stats["avg_mood"],
            "avg_sleep_hours": stats["avg_sleep_hours"],
            "narrative_summary": narrative,
            "raw_report_json": json.dumps(raw),
            "generated_at": now,
            "persona_at_generation": persona,
        },
    )
    await db.commit()

    return {
        "report_id": str(report_id),
        "user_id": str(user_id),
        "period": period,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "stats": stats,
        "narrative": narrative,
        "generated_at": now.isoformat(),
        "cached": False,
    }


# ─── Cache check ─────────────────────────────────────────────────

async def _get_cached_report(
    user_id: uuid.UUID,
    period: str,
    period_start: date,
    db: AsyncSession,
) -> Optional[dict]:
    """Return a cached report if it exists and is < 24 hours old."""
    from sqlalchemy import text
    import json

    result = await db.execute(
        text("""
            SELECT id, period_start, period_end, avg_daily_calories, avg_protein_g,
                   weight_start_kg, weight_end_kg, weight_delta_kg,
                   workouts_completed, avg_energy, avg_mood, avg_sleep_hours,
                   narrative_summary, raw_report_json, generated_at, persona_at_generation
            FROM reports
            WHERE user_id = :user_id
              AND period = :period
              AND period_start = :period_start
            ORDER BY generated_at DESC
            LIMIT 1
        """),
        {"user_id": user_id, "period": period, "period_start": period_start},
    )
    row = result.fetchone()
    if not row:
        return None

    age = datetime.now(timezone.utc) - row.generated_at.replace(tzinfo=timezone.utc)
    if age.total_seconds() > 86400:  # 24 hours
        return None

    raw = row.raw_report_json or {}
    return {
        "report_id": None,
        "user_id": str(user_id),
        "period": period,
        "period_start": row.period_start.isoformat(),
        "period_end": row.period_end.isoformat(),
        "stats": raw.get("stats", {}),
        "narrative": row.narrative_summary,
        "generated_at": row.generated_at.isoformat(),
        "cached": True,
    }


# ─── Public API ──────────────────────────────────────────────────

async def generate_weekly_report(user_id_str: str, db: AsyncSession) -> dict:
    user_id = uuid.UUID(user_id_str)
    today = date.today()
    # Current week: last 7 days (ending today exclusive = tomorrow)
    week_end = today + timedelta(days=1)
    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)

    cached = await _get_cached_report(user_id, "weekly", week_start, db)
    if cached:
        return cached

    # Load user context
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id_str} not found")

    result = await db.execute(select(UserHealthProfile).where(UserHealthProfile.user_id == user_id))
    health_profile = result.scalar_one_or_none()

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == user_id))
    persona_config = result.scalar_one_or_none()
    persona = persona_config.active_persona if persona_config else "friend"

    goal = health_profile.primary_goal if health_profile else "general_health"

    stats = await _aggregate_period(user_id, week_start, week_end, db)
    prev_stats = await _aggregate_period(user_id, prev_start, week_start, db)

    narrative = await _write_narrative(
        stats, prev_stats,
        user.full_name.split()[0], goal, persona, user.language,
        "week",
    )

    return await _save_report(
        user_id, "weekly", week_start, week_end - timedelta(days=1),
        stats, narrative, persona, db,
    )


async def generate_monthly_report(user_id_str: str, db: AsyncSession) -> dict:
    user_id = uuid.UUID(user_id_str)
    today = date.today()
    month_end = today + timedelta(days=1)
    month_start = today - timedelta(days=29)
    prev_start = month_start - timedelta(days=30)

    cached = await _get_cached_report(user_id, "monthly", month_start, db)
    if cached:
        return cached

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id_str} not found")

    result = await db.execute(select(UserHealthProfile).where(UserHealthProfile.user_id == user_id))
    health_profile = result.scalar_one_or_none()

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == user_id))
    persona_config = result.scalar_one_or_none()
    persona = persona_config.active_persona if persona_config else "friend"

    goal = health_profile.primary_goal if health_profile else "general_health"

    stats = await _aggregate_period(user_id, month_start, month_end, db)
    prev_stats = await _aggregate_period(user_id, prev_start, month_start, db)

    narrative = await _write_narrative(
        stats, prev_stats,
        user.full_name.split()[0], goal, persona, user.language,
        "month",
    )

    return await _save_report(
        user_id, "monthly", month_start, month_end - timedelta(days=1),
        stats, narrative, persona, db,
    )
