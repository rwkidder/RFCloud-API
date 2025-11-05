from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from app.db_async import get_async_db
from app import models

router = APIRouter(prefix="/async/links", tags=["Async Reporting"])

@router.get("/results/{link_id}", summary="Get latest link analysis with node details (async)")
async def get_link_results(link_id: int, db: AsyncSession = Depends(get_async_db)):
    # 1️⃣ Define aliases for node_a and node_b
    NodeA = aliased(models.TopologyNode)
    NodeB = aliased(models.TopologyNode)

    # 2️⃣ Fetch link with both nodes using a single async SELECT
    stmt = (
        select(models.TopologyLink, NodeA, NodeB)
        .join(NodeA, models.TopologyLink.node_a == NodeA.id)
        .join(NodeB, models.TopologyLink.node_b == NodeB.id)
        .where(models.TopologyLink.id == link_id)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Link or nodes not found")

    link, node_a, node_b = row

    # 3️⃣ Get the most recent RFLinkResult for this link
    result_stmt = (
        select(models.RFLinkResult)
        .where(models.RFLinkResult.link_id == link_id)
        .order_by(desc(models.RFLinkResult.calculated_at))
        .limit(1)
    )
    latest_result = (await db.execute(result_stmt)).scalar_one_or_none()

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
            "id": latest_result.id if latest_result else None,
            "fspl_db": latest_result.fspl_db if latest_result else None,
            "received_power_dbm": latest_result.received_power_dbm if latest_result else None,
            "link_margin_db": latest_result.link_margin_db if latest_result else None,
            "fresnel_clearance_m": latest_result.fresnel_clearance_m if latest_result else None,
            "is_clear": latest_result.is_clear if latest_result else None,
            "calculated_at": latest_result.calculated_at.isoformat() if latest_result else None,
        },
    }

    return response
