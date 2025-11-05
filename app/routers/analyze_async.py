from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_async import get_async_db
from app import models
import math
from datetime import datetime

router = APIRouter(prefix="/async/links", tags=["Async Analysis"])


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two coordinates in km."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/analyze/{link_id}")
async def analyze_link_async(link_id: int, db: AsyncSession = Depends(get_async_db)):
    """Asynchronously analyze a radio link and insert calculated metrics."""
    # --- Load link and associated nodes ---
    result = await db.execute(
        select(models.TopologyLink).where(models.TopologyLink.id == link_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail=f"Link {link_id} not found")

    node_a = await db.get(models.TopologyNode, link.node_a)
    node_b = await db.get(models.TopologyNode, link.node_b)
    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="Missing node(s) for link")

    # --- Radio link math ---
    d_km = haversine_km(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
    if d_km <= 0:
        raise HTTPException(status_code=422, detail="Invalid node coordinates")

    f_mhz = link.band_mhz
    f_ghz = f_mhz / 1000.0
    fspl = 20 * math.log10(d_km) + 20 * math.log10(f_mhz) + 32.44
    rx_pwr = link.tx_power_dbm - fspl
    margin = rx_pwr - (-90.0)
    r1_m = 17.32 * math.sqrt(d_km / f_ghz)
    is_clear = r1_m > 0

    # --- Store result ---
    rf_result = models.RFLinkResult(
        link_id=link.id,
        fspl_db=round(fspl, 2),
        received_power_dbm=round(rx_pwr, 2),
        link_margin_db=round(margin, 2),
        fresnel_clearance_m=round(r1_m, 2),
        is_clear=is_clear,
        calculated_at=datetime.utcnow()
    )

    db.add(rf_result)
    await db.commit()
    await db.refresh(rf_result)

    return rf_result
