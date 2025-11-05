# app/routers/plot.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from io import BytesIO
import matplotlib.pyplot as plt
import math
import httpx  # async alternative to requests
from app.db_async import get_async_db
from app import models

router = APIRouter(prefix="/plot", tags=["Visualization"])


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/link/{link_id}", summary="Plot terrain and Fresnel clearance (async)")
async def plot_link(link_id: int, db: AsyncSession = Depends(get_async_db)):
    # --- Fetch link and nodes ---
    link = await db.scalar(select(models.TopologyLink).where(models.TopologyLink.id == link_id))
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    node_a = await db.scalar(select(models.TopologyNode).where(models.TopologyNode.id == link.node_a))
    node_b = await db.scalar(select(models.TopologyNode).where(models.TopologyNode.id == link.node_b))
    if not node_a or not node_b:
        raise HTTPException(status_code=400, detail="Nodes missing")

    # --- Compute link geometry ---
    d_km = haversine_km(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
    d_m = d_km * 1000
    f_ghz = link.band_mhz / 1000.0
    r1_m = 17.32 * math.sqrt(d_km / f_ghz) if (d_km > 0 and f_ghz > 0) else 0.0

    # --- Terrain sampling ---
    num_samples = 20
    lat_step = (node_b.lat - node_a.lat) / (num_samples - 1)
    lon_step = (node_b.lon - node_a.lon) / (num_samples - 1)
    coords = [{"latitude": node_a.lat + i * lat_step, "longitude": node_a.lon + i * lon_step}
              for i in range(num_samples)]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post("https://api.open-elevation.com/api/v1/lookup", json={"locations": coords})
            r.raise_for_status()
            elevations = [p["elevation"] for p in r.json()["results"]]
    except Exception:
        elevations = [(node_a.elev + node_b.elev) / 2.0] * num_samples

    # --- Earth curvature & LOS ---
    R_earth = 6371000
    step_m = d_m / (num_samples - 1)
    bulges = [((i * step_m - d_m / 2) ** 2) / (2 * R_earth) for i in range(num_samples)]
    los_heights = [node_a.elev + (node_b.elev - node_a.elev) * (i / (num_samples - 1)) for i in range(num_samples)]
    terrain_adj = [elevations[i] + bulges[i] for i in range(num_samples)]

    # --- Clearance and result flag ---
    clearances = [los_heights[i] - terrain_adj[i] - r1_m for i in range(num_samples)]
    clearance_m = min(clearances)
    is_clear = clearance_m > 0

    # --- Plot ---
    x_vals = [i * d_m / (num_samples - 1) / 1000 for i in range(num_samples)]
    plt.figure(figsize=(8, 4))
    plt.fill_between(x_vals, terrain_adj, color="tan", alpha=0.6, label="Terrain + curvature")
    plt.plot(x_vals, los_heights, "k--", lw=1.2, label="Line-of-sight")
    plt.plot(x_vals, [h - r1_m for h in los_heights], "b:", lw=0.8)
    plt.plot(x_vals, [h + r1_m for h in los_heights], "b:", lw=0.8, label="Fresnel zone")
    plt.xlabel("Distance (km)")
    plt.ylabel("Elevation (m)")
    plt.title(f"Link {link.id}: {node_a.label} → {node_b.label}\nClear: {is_clear} | Min clearance {clearance_m:.1f} m")
    plt.legend(fontsize="small")
    plt.grid(True, linestyle=":")
    plt.tight_layout()

    # --- Return as PNG ---
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
