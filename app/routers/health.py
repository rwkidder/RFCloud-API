# app/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db_async import get_async_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", summary="Service and database health check")
async def health_check(db: AsyncSession = Depends(get_async_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        version = result.scalar_one()
        return {"status": "ok", "database": "connected", "version": version}
    except Exception as e:
        return {"status": "error", "database": "unreachable", "detail": str(e)}
