# app/routers/project_analysis.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_async import get_async_db
from app import models

router = APIRouter(prefix="/async/projects", tags=["Async Project Analysis"])


@router.get("/{project_id}/summary", summary="Get async link performance summary for a project")
async def summarize_project(project_id: int, db: AsyncSession = Depends(get_async_db)):
    # 1️⃣ Fetch project links
    result_links = await db.execute(
        select(models.TopologyLink).where(models.TopologyLink.project_id == project_id)
    )
    links = result_links.scalars().all()
    if not links:
        raise HTTPException(status_code=404, detail="No links found for this project")

    # 2️⃣ Aggregate RFLinkResult stats using SQLAlchemy 2.x Core style
    stmt = (
        select(
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
        .where(models.TopologyLink.project_id == project_id)
    )

    result_stats = await db.execute(stmt)
    stats = result_stats.one_or_none()

    if not stats:
        raise HTTPException(status_code=404, detail="No analysis results found")

    # 3️⃣ Compute ratios and prepare response
    summary = {
        "project_id": project_id,
        "link_count": len(links),
        "avg_margin_db": round(stats.avg_margin or 0, 2),
        "clear_ratio": round(((stats.clear_links or 0) / len(links)), 2),
        "results_recorded": stats.n_results or 0,
    }

    return summary
