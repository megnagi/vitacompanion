from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import DailyLog
from models.log import MealLog, WorkoutLog
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import uuid


# ─── Request Schemas ────────────────────────────────────────────

class DailyLogRequest(BaseModel):
    user_id: str
    log_date: date

    # Weight
    weight_kg: Optional[float] = None

    # Nutrition totals
    calories_total: Optional[int] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    water_ml: Optional[int] = None

    # Training
    workout_completed: Optional[bool] = None
    workout_skipped: Optional[bool] = False
    skip_reason: Optional[str] = None

    # Subjective
    energy_level: Optional[int] = None   # 1-5
    mood_score: Optional[int] = None     # 1-5
    sleep_hours: Optional[float] = None

    # Pain / safety
    pain_reported: bool = False
    pain_detail: Optional[str] = None

    notes: Optional[str] = None

    @field_validator("weight_kg")
    @classmethod
    def weight_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("weight_kg must be >= 0")
        return v

    @field_validator("sleep_hours")
    @classmethod
    def sleep_hours_range(cls, v):
        if v is not None and not (0 <= v <= 24):
            raise ValueError("sleep_hours must be between 0 and 24")
        return v


class MealLogRequest(BaseModel):
    user_id: str
    log_date: date
    meal_type: str                        # breakfast | lunch | dinner | snack
    description: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    on_plan: Optional[bool] = None
    notes: Optional[str] = None

    @field_validator("calories", "protein_g", "fat_g", "carbs_g")
    @classmethod
    def nutrition_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("nutrition values must be >= 0")
        return v


class WorkoutLogRequest(BaseModel):
    user_id: str
    log_date: date
    session_type: str                     # cardio | strength | mobility | rest | active_recovery
    planned_duration_min: Optional[int] = None
    actual_duration_min: Optional[int] = None
    intensity: Optional[str] = None
    avg_hr_bpm: Optional[int] = None
    max_hr_bpm: Optional[int] = None
    hr_zone_target: Optional[str] = None
    hr_zone_exceeded: bool = False
    exercises: Optional[list] = None
    perceived_exertion: Optional[int] = None  # 1-10
    pain_during: bool = False
    pain_detail: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("perceived_exertion")
    @classmethod
    def exertion_range(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError("perceived_exertion must be between 1 and 10")
        return v


# ─── Response Schemas ────────────────────────────────────────────

class DailyLogResponse(BaseModel):
    log_id: str
    user_id: str
    log_date: date
    message: str


class MealLogResponse(BaseModel):
    meal_log_id: str
    user_id: str
    log_date: date
    meal_type: str
    message: str


class WorkoutLogResponse(BaseModel):
    workout_log_id: str
    user_id: str
    log_date: date
    session_type: str
    message: str


# ─── Helper: get or create daily log ────────────────────────────

async def get_or_create_daily_log(
    user_id: uuid.UUID,
    log_date: date,
    db: AsyncSession
) -> DailyLog:
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id,
            DailyLog.log_date == log_date
        )
    )
    daily_log = result.scalar_one_or_none()

    if not daily_log:
        now = datetime.now(timezone.utc)
        daily_log = DailyLog(
            id=uuid.uuid4(),
            user_id=user_id,
            log_date=log_date,
            pain_reported=False,
            safety_flag_raised=False,
            flag_type="none",
            created_at=now,
            updated_at=now,
        )
        db.add(daily_log)
        await db.flush()

    return daily_log


# ─── Service: Daily Log ──────────────────────────────────────────

async def upsert_daily_log(
    data: DailyLogRequest,
    db: AsyncSession
) -> DailyLogResponse:
    now = datetime.now(timezone.utc)
    user_id = uuid.UUID(data.user_id)

    daily_log = await get_or_create_daily_log(user_id, data.log_date, db)

    # Update fields if provided
    if data.weight_kg is not None:
        daily_log.weight_kg = data.weight_kg
        daily_log.weight_logged_at = now
    if data.calories_total is not None:
        daily_log.calories_total = data.calories_total
    if data.protein_g is not None:
        daily_log.protein_g = data.protein_g
    if data.fat_g is not None:
        daily_log.fat_g = data.fat_g
    if data.carbs_g is not None:
        daily_log.carbs_g = data.carbs_g
    if data.water_ml is not None:
        daily_log.water_ml = data.water_ml
    if data.workout_completed is not None:
        daily_log.workout_completed = data.workout_completed
    if data.workout_skipped is not None:
        daily_log.workout_skipped = data.workout_skipped
    if data.skip_reason is not None:
        daily_log.skip_reason = data.skip_reason
    if data.energy_level is not None:
        daily_log.energy_level = data.energy_level
    if data.mood_score is not None:
        daily_log.mood_score = data.mood_score
    if data.sleep_hours is not None:
        daily_log.sleep_hours = data.sleep_hours
    if data.pain_reported:
        daily_log.pain_reported = True
        daily_log.pain_detail = data.pain_detail
        daily_log.safety_flag_raised = True
        daily_log.flag_type = "physical"
    if data.notes is not None:
        daily_log.notes = data.notes

    daily_log.updated_at = now
    await db.commit()

    return DailyLogResponse(
        log_id=str(daily_log.id),
        user_id=data.user_id,
        log_date=data.log_date,
        message="Daily log saved."
    )


# ─── Service: Meal Log ───────────────────────────────────────────

async def create_meal_log(
    data: MealLogRequest,
    db: AsyncSession
) -> MealLogResponse:
    now = datetime.now(timezone.utc)
    user_id = uuid.UUID(data.user_id)

    daily_log = await get_or_create_daily_log(user_id, data.log_date, db)

    meal_log = MealLog(
        id=uuid.uuid4(),
        user_id=user_id,
        daily_log_id=daily_log.id,
        log_date=data.log_date,
        meal_type=data.meal_type,
        logged_at=now,
        description=data.description,
        calories=data.calories,
        protein_g=data.protein_g,
        fat_g=data.fat_g,
        carbs_g=data.carbs_g,
        on_plan=data.on_plan,
        notes=data.notes,
    )
    db.add(meal_log)

    # Update daily totals
    if data.calories:
        daily_log.calories_total = int(daily_log.calories_total or 0) + data.calories
    if data.protein_g:
        daily_log.protein_g = float(daily_log.protein_g or 0) + data.protein_g
    if data.fat_g:
        daily_log.fat_g = float(daily_log.fat_g or 0) + data.fat_g
    if data.carbs_g:
        daily_log.carbs_g = float(daily_log.carbs_g or 0) + data.carbs_g

    daily_log.updated_at = now
    await db.commit()

    return MealLogResponse(
        meal_log_id=str(meal_log.id),
        user_id=data.user_id,
        log_date=data.log_date,
        meal_type=data.meal_type,
        message=f"{data.meal_type.capitalize()} logged successfully."
    )


# ─── Service: Workout Log ────────────────────────────────────────

async def create_workout_log(
    data: WorkoutLogRequest,
    db: AsyncSession
) -> WorkoutLogResponse:
    now = datetime.now(timezone.utc)
    user_id = uuid.UUID(data.user_id)

    daily_log = await get_or_create_daily_log(user_id, data.log_date, db)

    workout_log = WorkoutLog(
        id=uuid.uuid4(),
        user_id=user_id,
        daily_log_id=daily_log.id,
        log_date=data.log_date,
        session_type=data.session_type,
        planned_duration_min=data.planned_duration_min,
        actual_duration_min=data.actual_duration_min,
        intensity=data.intensity,
        avg_hr_bpm=data.avg_hr_bpm,
        max_hr_bpm=data.max_hr_bpm,
        hr_zone_target=data.hr_zone_target,
        hr_zone_exceeded=data.hr_zone_exceeded,
        exercises=data.exercises,
        perceived_exertion=data.perceived_exertion,
        pain_during=data.pain_during,
        pain_detail=data.pain_detail,
        notes=data.notes,
        logged_at=now,
    )
    db.add(workout_log)

    # Mark workout completed on daily log
    daily_log.workout_completed = True
    daily_log.updated_at = now

    # Safety flag if pain reported
    if data.pain_during:
        daily_log.pain_reported = True
        daily_log.safety_flag_raised = True
        daily_log.flag_type = "physical"

    await db.commit()

    return WorkoutLogResponse(
        workout_log_id=str(workout_log.id),
        user_id=data.user_id,
        log_date=data.log_date,
        session_type=data.session_type,
        message=f"{data.session_type.capitalize()} session logged successfully."
    )