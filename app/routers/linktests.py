from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app import models

router = APIRouter(prefix="/links", tags=["Reporting"])

@router.get("/results/{link_id}", summary="Get latest link analysis with node details")
def get_link_results(link_id: int, db: Session = Depends(get_db)):
    # 1️⃣ Fetch link
    link = db.query(models.TopologyLink).filter(models.TopologyLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 2️⃣ Fetch related nodes
    node_a = db.query(models.TopologyNode).filter(models.TopologyNode.id == link.node_a).first()
    node_b = db.query(models.TopologyNode).filter(models.TopologyNode.id == link.node_b).first()

    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="Nodes not found for link")

    # 3️⃣ Get most recent result
    result = (
        db.query(models.RFLinkResult)
        .filter(models.RFLinkResult.link_id == link_id)
        .order_by(desc(models.RFLinkResult.calculated_at))
        .first()
    )

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
            "id": result.id if result else None,
            "fspl_db": result.fspl_db if result else None,
            "received_power_dbm": result.received_power_dbm if result else None,
            "link_margin_db": result.link_margin_db if result else None,
            "fresnel_clearance_m": result.fresnel_clearance_m if result else None,
            "is_clear": result.is_clear if result else None,
            "calculated_at": result.calculated_at.isoformat() if result else None,
        },
    }

    return response
