# app/routers/analyze.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
import math
import requests

router = APIRouter(prefix="/links", tags=["Analysis"])

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/analyze/{link_id}")
def analyze_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(models.TopologyLink).filter(models.TopologyLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    node_a = db.query(models.TopologyNode).filter(models.TopologyNode.id == link.node_a).first()
    node_b = db.query(models.TopologyNode).filter(models.TopologyNode.id == link.node_b).first()
    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="Missing node(s) for link")

    # Distance in km
    d_km = haversine_km(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
    f_mhz = link.band_mhz

    # Free-space path loss (dB)
    fspl = 20 * math.log10(d_km) + 20 * math.log10(f_mhz) + 32.44 if d_km > 0 else 0.0

    # Received power (simple form)
    rx_pwr = link.tx_power_dbm - fspl

    # Margin vs nominal -90 dBm sensitivity
    margin = rx_pwr - (-90.0)

    # Fresnel zone radius at mid-path (m)
    f_ghz = f_mhz / 1000.0
    r1_m = 17.32 * math.sqrt(d_km / f_ghz) if (d_km > 0 and f_ghz > 0) else 0.0

    # 🌍 Terrain sampling with Open-Elevation
    num_samples = 10  # more samples → smoother profile
    lat_step = (node_b.lat - node_a.lat) / (num_samples - 1)
    lon_step = (node_b.lon - node_a.lon) / (num_samples - 1)

    coords = [{"latitude": node_a.lat + i * lat_step, "longitude": node_a.lon + i * lon_step}
              for i in range(num_samples)]

    try:
        r = requests.post("https://api.open-elevation.com/api/v1/lookup", json={"locations": coords}, timeout=10)
        r.raise_for_status()
        elevations = [p["elevation"] for p in r.json()["results"]]
    except Exception as e:
        # fallback if API fails → use average node elevations
        elevations = [(node_a.elev + node_b.elev) / 2.0] * num_samples

    # Earth curvature correction at each point (meters)
    R_earth = 6371000
    d_m = d_km * 1000
    step_m = d_m / (num_samples - 1)
    bulges = [((i * step_m - d_m / 2) ** 2) / (2 * R_earth) for i in range(num_samples)]

    # Line-of-sight height at each sample
    los_heights = [node_a.elev + (node_b.elev - node_a.elev) * (i / (num_samples - 1)) for i in range(num_samples)]

    # Check clearance above terrain + curvature + Fresnel
    clearances = [los_heights[i] - elevations[i] - bulges[i] - r1_m for i in range(num_samples)]
    clearance_m = min(clearances)
    is_clear = clearance_m > 0


    # Store result
    result = models.RFLinkResult(
        link_id=link.id,
        fspl_db=round(fspl, 2),
        received_power_dbm=round(rx_pwr, 2),
        link_margin_db=round(margin, 2),
        fresnel_clearance_m=round(clearance_m, 2),
        is_clear=is_clear
    )

    db.add(result)
    db.commit()
    db.refresh(result)
    return result
