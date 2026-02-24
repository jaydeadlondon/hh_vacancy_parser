from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Базовая проверка — сервис живой"""
    return {"status": "ok", "service": "api-gateway"}


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Проверка подключения к БД"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
