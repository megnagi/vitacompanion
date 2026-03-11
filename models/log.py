from sqlalchemy import Column, String, Date, Numeric, Boolean, Text, ARRAY, Integer, SmallInteger, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
import uuid
from db import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    daily_log_id = Column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    meal_type = Column(String, nullable=False)  # breakfast | lunch | dinner | snack
    logged_at = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=False)
    calories = Column(Integer, nullable=True)
    protein_g = Column(Numeric(5, 1), nullable=True)
    fat_g = Column(Numeric(5, 1), nullable=True)
    carbs_g = Column(Numeric(5, 1), nullable=True)
    on_plan = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)

    daily_log = relationship("DailyLog", back_populates="meal_logs")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    daily_log_id = Column(UUID(as_uuid=True), ForeignKey("daily_logs.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    session_type = Column(ENUM('cardio', 'strength', 'mobility', 'rest', 'active_recovery', name='session_type', create_type=False), nullable=False)
    planned_duration_min = Column(Integer, nullable=True)
    actual_duration_min = Column(Integer, nullable=True)
    intensity = Column(ENUM('low', 'moderate', 'moderate_high', 'high', name='intensity_level', create_type=False), nullable=True)
    avg_hr_bpm = Column(Integer, nullable=True)
    max_hr_bpm = Column(Integer, nullable=True)
    hr_zone_target = Column(String, nullable=True)
    hr_zone_exceeded = Column(Boolean, default=False)
    exercises = Column(JSONB, nullable=True)
    perceived_exertion = Column(SmallInteger, nullable=True)
    pain_during = Column(Boolean, default=False)
    pain_detail = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), nullable=False)

    daily_log = relationship("DailyLog", back_populates="workout_logs")