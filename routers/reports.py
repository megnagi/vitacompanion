from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from services.report_service import generate_weekly_report, generate_monthly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly/{user_id}", status_code=status.HTTP_200_OK)
async def weekly_report(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await generate_weekly_report(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly/{user_id}", status_code=status.HTTP_200_OK)
async def monthly_report(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await generate_monthly_report(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
