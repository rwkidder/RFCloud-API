from fastapi import APIRouter
from pydantic import BaseModel, Field
import math

router = APIRouter(prefix="/calc", tags=["Calculations"])

class FresnelInput(BaseModel):
    distance_km: float = Field(..., description="Total distance between antennas (km)")
    freq_mhz: float = Field(..., description="Frequency in MHz")
    h_tx_m: float = Field(..., description="Height of transmitting antenna (m)")
    h_rx_m: float = Field(..., description="Height of receiving antenna (m)")
    obstacle_distance_km: float = Field(..., description="Distance to obstacle from transmitter (km)")
    obstacle_height_m: float = Field(..., description="Height of the obstacle (m)")
    zone_number: int = Field(1, description="Fresnel zone number (1 for first zone, 2 for second, etc.)")

class FresnelResult(BaseModel):
    zone_radius_m: float
    clearance_m: float
    is_clear: bool

@router.post("/fresnel", response_model=FresnelResult)
def calc_fresnel(data: FresnelInput):
    """
    Compute Fresnel zone radius and clearance.
    zone_number allows calculation of higher-order zones.
    """
    d1 = data.obstacle_distance_km
    d2 = data.distance_km - d1
    wavelength_m = 300 / data.freq_mhz  # meters

    # Fresnel zone radius formula (includes full first-zone scaling)
    zone_radius = math.sqrt((data.zone_number * wavelength_m * d1 * d2 * 1000) / (data.distance_km))

    # Line-of-sight interpolation at obstacle point
    los_height = data.h_tx_m + (data.h_rx_m - data.h_tx_m) * (d1 / data.distance_km)

    clearance = los_height - data.obstacle_height_m - zone_radius
    is_clear = clearance > 0

    return FresnelResult(
        zone_radius_m=round(zone_radius, 2),
        clearance_m=round(clearance, 2),
        is_clear=is_clear
    )
