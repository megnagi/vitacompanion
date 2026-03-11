import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
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
    try:
        return StreamingResponse(
            stream_chat(data, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
