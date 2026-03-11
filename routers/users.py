from fastapi import APIRouter, Depends, HTTPException, status
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