from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db import get_db
from app import models

router = APIRouter(prefix="/projects", tags=["Project Analysis"])

@router.get("/{project_id}/summary", summary="Get link performance summary for a project")
def summarize_project(project_id: int, db: Session = Depends(get_db)):
    links = db.query(models.TopologyLink).filter(models.TopologyLink.project_id == project_id).all()
    if not links:
        raise HTTPException(status_code=404, detail="No links found for this project")

    # Count how many results per link

    stats = (
        db.query(
            func.count(models.RFLinkResult.id).label("n_results"),
            func.avg(models.RFLinkResult.link_margin_db).label("avg_margin"),
            func.sum(
                case(
                    (models.RFLinkResult.is_clear.is_(True), 1),
                    else_=0
                )
            ).label("clear_links"),
        )
        .join(models.TopologyLink, models.TopologyLink.id == models.RFLinkResult.link_id)
        .filter(models.TopologyLink.project_id == project_id)
        .first()
    )


    summary = {
    "project_id": project_id,
    "link_count": len(links),
    "avg_margin_db": round(stats.avg_margin or 0, 2),
    "clear_ratio": round(((stats.clear_links or 0) / len(links)), 2),
    "results_recorded": stats.n_results or 0,
    }

    return summary
