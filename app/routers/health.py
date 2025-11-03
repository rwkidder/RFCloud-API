from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", summary="Simple service and database health check")
def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute("SELECT version();").scalar()
        return {"status": "ok", "database": "connected", "version": result}
    except Exception as e:
        return {"status": "error", "database": "unreachable", "detail": str(e)}
