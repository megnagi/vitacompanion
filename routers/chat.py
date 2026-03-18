import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db
from services.chat_service import ChatRequest, stream_chat

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Send a message and stream a coached response (SSE)",
)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Validate user + profile BEFORE creating StreamingResponse.
    # StreamingResponse sends 200 headers before the generator runs, so
    # any ValueError raised inside the generator cannot change the status code.
    from models.user import User, UserHealthProfile, UserPersonaConfig
    try:
        uid = uuid.UUID(data.user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid user_id")

    result = await db.execute(select(User).where(User.id == uid))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"User {data.user_id} not found")

    result = await db.execute(select(UserHealthProfile).where(UserHealthProfile.user_id == uid))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Health profile not found for user {data.user_id}")

    result = await db.execute(select(UserPersonaConfig).where(UserPersonaConfig.user_id == uid))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Persona config not found for user {data.user_id}")

    try:
        return StreamingResponse(
            stream_chat(data, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
