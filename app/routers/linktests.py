from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_async import get_async_db
from app import models

router = APIRouter(prefix="/async/links", tags=["Async Reporting"])

@router.get("/results/{link_id}", summary="Get latest link analysis with node details (async)")
async def get_link_results_async(link_id: int, db: AsyncSession = Depends(get_async_db)):
    # 1️⃣ Fetch link
    result = await db.execute(select(models.TopologyLink).where(models.TopologyLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 2️⃣ Fetch related nodes
    node_a = await db.get(models.TopologyNode, link.node_a)
    node_b = await db.get(models.TopologyNode, link.node_b)
    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="Nodes not found for link")

    # 3️⃣ Get most recent result
    result = await db.execute(
        select(models.RFLinkResult)
        .where(models.RFLinkResult.link_id == link_id)
        .order_by(desc(models.RFLinkResult.calculated_at))
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    # 4️⃣ Construct response JSON
    response = {
        "link": {
            "id": link.id,
            "band_mhz": link.band_mhz,
            "bw_khz": link.bw_khz,
            "modulation": link.modulation,
            "tx_power_dbm": link.tx_power_dbm,
            "notes": link.notes,
        },
        "node_a": {
            "id": node_a.id,
            "label": node_a.label,
            "lat": node_a.lat,
            "lon": node_a.lon,
            "elev": node_a.elev,
            "radio_profile": node_a.radio_profile,
        },
        "node_b": {
            "id": node_b.id,
            "label": node_b.label,
            "lat": node_b.lat,
            "lon": node_b.lon,
            "elev": node_b.elev,
            "radio_profile": node_b.radio_profile,
        },
        "analysis": {
            "id": latest.id if latest else None,
            "fspl_db": latest.fspl_db if latest else None,
            "received_power_dbm": latest.received_power_dbm if latest else None,
            "link_margin_db": latest.link_margin_db if latest else None,
            "fresnel_clearance_m": latest.fresnel_clearance_m if latest else None,
            "is_clear": latest.is_clear if latest else None,
            "calculated_at": latest.calculated_at.isoformat() if latest else None,
        },
    }

    return response
