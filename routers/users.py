from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from services.user_service import OnboardingRequest, OnboardingResponse, create_user_onboarding

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/onboard",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new user after SSO",
)
async def onboard_user(
    data: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    try:
        result = await create_user_onboarding(data, db)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/by-email/{email}",
    summary="Get user by email (used by SSO sync)",
)
async def get_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from models.user import User

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "user_id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "persona": user.persona_config.active_persona if user.persona_config else "friend",
    }


@router.get(
    "/{user_id}",
    summary="Get user by ID",
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from models.user import User
    import uuid

    try:
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return {
            "user_id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "persona": user.persona_config.active_persona if user.persona_config else "friend",
            "onboarded_at": user.onboarded_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


class PersonaSwitchRequest(BaseModel):
    persona: str   # 'friend' | 'coach' | 'commander'
    reason: str | None = None


@router.post(
    "/{user_id}/persona/switch",
    summary="Switch active persona for a user",
)
async def switch_persona(
    user_id: str,
    data: PersonaSwitchRequest,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from models.user import User, UserPersonaConfig, PersonaSwitchLog
    from datetime import datetime, timezone
    import uuid

    valid = {"friend", "coach", "commander"}
    if data.persona not in valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"persona must be one of {sorted(valid)}",
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user_id")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == uid))
    persona_config = result.scalar_one_or_none()
    if not persona_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona config not found")

    now = datetime.now(timezone.utc)
    from_persona = persona_config.active_persona

    persona_config.active_persona = data.persona
    persona_config.switched_at = now

    log_entry = PersonaSwitchLog(
        id=uuid.uuid4(),
        user_id=uid,
        from_persona=from_persona,
        to_persona=data.persona,
        reason=data.reason,
        switched_at=now,
    )
    db.add(log_entry)
    await db.commit()

    return {
        "user_id": user_id,
        "active_persona": data.persona,
        "previous_persona": from_persona,
    }
