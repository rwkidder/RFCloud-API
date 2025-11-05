from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db_async import get_async_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", summary="Simple service and database health check")
def health_check(db: Session = Depends(get_async_db)):
    try:
        result =conn.execute(text("SELECT version();"))
        return {"status": "ok", "database": "connected", "version": result}
    except Exception as e:
        return {"status": "error", "database": "unreachable", "detail": str(e)}
