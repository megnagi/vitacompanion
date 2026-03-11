from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db
from services.log_service import (
    DailyLogRequest, DailyLogResponse, upsert_daily_log,
    MealLogRequest, MealLogResponse, create_meal_log,
    WorkoutLogRequest, WorkoutLogResponse, create_workout_log,
)
from models.user import DailyLog
import uuid

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
)


@router.post(
    "/daily",
    response_model=DailyLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a daily log",
)
async def log_daily(
    data: DailyLogRequest,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    try:
        return await upsert_daily_log(data, db)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/meal",
    response_model=MealLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a meal",
)
async def log_meal(
    data: MealLogRequest,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    try:
        return await create_meal_log(data, db)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/workout",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a workout session",
)
async def log_workout(
    data: WorkoutLogRequest,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    try:
        return await create_workout_log(data, db)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/daily/{user_id}/{log_date}",
    summary="Get a daily log by user and date",
)
async def get_daily_log(
    user_id: str,
    log_date: str,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    from datetime import date
    try:
        parsed_date = date.fromisoformat(log_date)
        result = await db.execute(
            select(DailyLog).where(
                DailyLog.user_id == uuid.UUID(user_id),
                DailyLog.log_date == parsed_date,
            )
        )
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="No log found for this date.")
        return {
            "log_id": str(log.id),
            "user_id": str(log.user_id),
            "log_date": str(log.log_date),
            "weight_kg": float(log.weight_kg) if log.weight_kg else None,
            "calories_total": log.calories_total,
            "protein_g": float(log.protein_g) if log.protein_g else None,
            "workout_completed": log.workout_completed,
            "energy_level": log.energy_level,
            "mood_score": log.mood_score,
            "sleep_hours": float(log.sleep_hours) if log.sleep_hours else None,
            "pain_reported": log.pain_reported,
            "safety_flag_raised": log.safety_flag_raised,
            "notes": log.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))