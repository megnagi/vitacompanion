from datetime import date, datetime, timezone, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User, UserHealthProfile, UserPersonaConfig, UserSchedulerState
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


# ─── Request Schemas ────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    # From SSO
    email: EmailStr
    full_name: str
    sso_provider: str          # 'google' | 'apple'
    sso_id: str
    avatar_url: Optional[str] = None

    # Step 1 — basic vitals
    date_of_birth: date
    sex: str                   # 'male' | 'female' | 'other'
    height_cm: float
    starting_weight_kg: float

    # Step 2 — goal
    primary_goal: str          # 'weight_loss' | 'muscle_gain' | 'maintenance' | 'endurance' | 'general_health'
    target_weight_kg: Optional[float] = None
    activity_level: str = "moderate"

    # Step 3 — medical (skippable)
    medical_conditions: Optional[list[str]] = None
    medications: Optional[list[str]] = None
    injuries: Optional[list[str]] = None

    # Step 4 — dietary (skippable)
    dietary_restrictions: Optional[list[str]] = None
    allergies: Optional[list[str]] = None

    # Step 5 — persona
    persona: str = "friend"    # 'friend' | 'coach' | 'commander'

    # Preferences
    timezone: str = "Asia/Jerusalem"
    language: str = "he"
    preferred_checkin_time: str = "08:00"


class OnboardingResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    persona: str
    message: str


# ─── Service Logic ───────────────────────────────────────────────

async def create_user_onboarding(
    data: OnboardingRequest,
    db: AsyncSession
) -> OnboardingResponse:

    # Check if user already exists (SSO re-login)
    existing = await db.execute(
        select(User).where(User.sso_id == data.sso_id)
    )
    existing_user = existing.scalar_one_or_none()

    if existing_user:
        return OnboardingResponse(
            user_id=str(existing_user.id),
            full_name=existing_user.full_name,
            email=existing_user.email,
            persona="friend",
            message="Welcome back!"
        )

    now = datetime.now(timezone.utc)

    # Parse preferred check-in time
    checkin_hour, checkin_minute = map(int, data.preferred_checkin_time.split(":"))
    checkin_time = time(checkin_hour, checkin_minute)

    # 1. Create user
    user = User(
        id=uuid.uuid4(),
        email=data.email,
        full_name=data.full_name,
        sso_provider=data.sso_provider,
        sso_id=data.sso_id,
        avatar_url=data.avatar_url,
        date_of_birth=data.date_of_birth,
        sex=data.sex,
        height_cm=data.height_cm,
        timezone=data.timezone,
        language=data.language,
        onboarded_at=now,
        created_at=now,
        updated_at=now,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    # 2. Create health profile
    health_profile = UserHealthProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        primary_goal=data.primary_goal,
        target_weight_kg=data.target_weight_kg,
        activity_level=data.activity_level,
        starting_weight_kg=data.starting_weight_kg,
        medical_conditions=data.medical_conditions,
        medications=data.medications,
        injuries=data.injuries,
        dietary_restrictions=data.dietary_restrictions,
        allergies=data.allergies,
        created_at=now,
        updated_at=now,
    )
    db.add(health_profile)

    # 3. Create persona config
    persona_config = UserPersonaConfig(
        id=uuid.uuid4(),
        user_id=user.id,
        active_persona=data.persona,
        humor_tolerance=5,
        praise_frequency=5,
        safety_override_active=True,
        switched_at=now,
        created_at=now,
    )
    db.add(persona_config)

    # 4. Create scheduler state
    scheduler_state = UserSchedulerState(
        id=uuid.uuid4(),
        user_id=user.id,
        preferred_checkin_time=checkin_time,
        next_checkin_at=now + timedelta(days=1),
        days_since_last_weigh_in=0,
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(7, 0),
        max_nudges_per_day=3,
        updated_at=now,
    )
    db.add(scheduler_state)

    # All four rows committed together as one transaction
    await db.commit()

    return OnboardingResponse(
        user_id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        persona=data.persona,
        message=f"Welcome to VitaCompanion, {user.full_name.split()[0]}! Your journey starts now."
    )