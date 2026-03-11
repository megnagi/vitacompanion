from sqlalchemy import Column, String, Date, Numeric, Boolean, Text, ARRAY, Integer, SmallInteger, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from db import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(ENUM('male', 'female', 'other', name='sex_type', create_type=False), nullable=False)
    height_cm = Column(Numeric(5, 1), nullable=False)
    timezone = Column(String, nullable=False, default="Asia/Jerusalem")
    language = Column(String, nullable=False, default="he")
    onboarded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    sso_provider = Column(String, nullable=True)
    sso_id = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Relationships
    health_profile = relationship("UserHealthProfile", back_populates="user", uselist=False)
    persona_config = relationship("UserPersonaConfig", back_populates="user", uselist=False)
    scheduler_state = relationship("UserSchedulerState", back_populates="user", uselist=False)
    daily_logs = relationship("DailyLog", back_populates="user")


class UserHealthProfile(Base):
    __tablename__ = "user_health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    primary_goal = Column(ENUM('weight_loss', 'muscle_gain', 'maintenance', 'endurance', 'general_health', name='goal_type',create_type=False), nullable=False)
    target_weight_kg = Column(Numeric(5, 1), nullable=True)
    activity_level = Column(ENUM('sedentary', 'light', 'moderate', 'active', 'very_active', name='activity_level', create_type=False), nullable=False, default="moderate")
    starting_weight_kg = Column(Numeric(5, 1), nullable=False)
    medical_conditions = Column(ARRAY(Text), nullable=True)
    medications = Column(ARRAY(Text), nullable=True)
    injuries = Column(ARRAY(Text), nullable=True)
    physician_clearance = Column(Boolean, nullable=False, default=False)
    dietary_restrictions = Column(ARRAY(Text), nullable=True)
    allergies = Column(ARRAY(Text), nullable=True)
    preferred_cuisines = Column(ARRAY(Text), nullable=True)
    blood_glucose_fasting = Column(Numeric(6, 2), nullable=True)
    hba1c = Column(Numeric(4, 2), nullable=True)
    cholesterol_ldl = Column(Numeric(6, 2), nullable=True)
    cholesterol_hdl = Column(Numeric(6, 2), nullable=True)
    triglycerides = Column(Numeric(6, 2), nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    bloodwork_date = Column(Date, nullable=True)
    past_barriers = Column(ARRAY(Text), nullable=True)
    motivators = Column(ARRAY(Text), nullable=True)
    emotional_triggers = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="health_profile")


class UserPersonaConfig(Base):
    __tablename__ = "user_persona_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    active_persona = Column(ENUM('friend', 'coach', 'commander', name='persona_style', create_type=False), nullable=False, default="friend")
    humor_tolerance = Column(SmallInteger, nullable=False, default=5)
    praise_frequency = Column(SmallInteger, nullable=False, default=5)
    custom_tone_notes = Column(Text, nullable=True)
    safety_override_active = Column(Boolean, nullable=False, default=True)
    switched_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="persona_config")


class UserSchedulerState(Base):
    __tablename__ = "user_scheduler_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    preferred_checkin_time = Column(Time, nullable=False)
    next_checkin_at = Column(DateTime(timezone=True), nullable=True)
    last_checkin_at = Column(DateTime(timezone=True), nullable=True)
    last_nudge_sent_at = Column(DateTime(timezone=True), nullable=True)
    days_since_last_weigh_in = Column(Integer, nullable=False, default=0)
    nudge_paused_until = Column(DateTime(timezone=True), nullable=True)
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)
    max_nudges_per_day = Column(SmallInteger, nullable=False, default=3)
    next_weekly_report_at = Column(DateTime(timezone=True), nullable=True)
    next_monthly_report_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="scheduler_state")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    weight_kg = Column(Numeric(5, 1), nullable=True)
    weight_logged_at = Column(DateTime(timezone=True), nullable=True)
    calories_total = Column(Integer, nullable=True)
    protein_g = Column(Numeric(6, 1), nullable=True)
    fat_g = Column(Numeric(6, 1), nullable=True)
    carbs_g = Column(Numeric(6, 1), nullable=True)
    water_ml = Column(Integer, nullable=True)
    calorie_target = Column(Integer, nullable=True)
    protein_target_g = Column(Numeric(6, 1), nullable=True)
    workout_completed = Column(Boolean, nullable=True)
    workout_skipped = Column(Boolean, default=False)
    skip_reason = Column(Text, nullable=True)
    energy_level = Column(SmallInteger, nullable=True)
    mood_score = Column(SmallInteger, nullable=True)
    sleep_hours = Column(Numeric(3, 1), nullable=True)
    pain_reported = Column(Boolean, nullable=False, default=False)
    pain_detail = Column(Text, nullable=True)
    safety_flag_raised = Column(Boolean, nullable=False, default=False)
    flag_type = Column(ENUM('none', 'physical', 'emotional', 'constraint_violation', 'rapid_weight_loss', 'pain_reported', 'hr_exceeded', 'overtraining_risk', 'medical_hold', name='flag_type', create_type=False), default="none")
    flag_detail = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="daily_logs")
    meal_logs = relationship("MealLog", back_populates="daily_log")
    workout_logs = relationship("WorkoutLog", back_populates="daily_log")