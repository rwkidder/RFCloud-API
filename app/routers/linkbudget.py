from fastapi import APIRouter
from pydantic import BaseModel, Field
import math

router = APIRouter(prefix="/calc", tags=["Calculations"])


# ---------- Input schema ----------
class LinkBudgetInput(BaseModel):
    tx_power_dbm: float = Field(..., description="Transmit power in dBm")
    freq_mhz: float = Field(..., description="Frequency in MHz")
    distance_km: float = Field(..., description="Path distance in kilometers")
    gain_tx_db: float = Field(0, description="Transmit antenna gain in dB")
    gain_rx_db: float = Field(0, description="Receive antenna gain in dB")
    system_loss_db: float = Field(0, description="Total system losses (cable, connectors, etc.) in dB")
    rx_sensitivity_dbm: float = Field(-90, description="Receiver sensitivity in dBm")


# ---------- Output schema ----------
class LinkBudgetResult(BaseModel):
    fspl_db: float
    received_power_dbm: float
    link_margin_db: float


# ---------- Endpoint ----------
@router.post("/linkbudget", response_model=LinkBudgetResult)
def calc_linkbudget(data: LinkBudgetInput):
    """Compute free-space path loss and link margin."""
    # FSPL (dB) = 20log10(d) + 20log10(f) + 32.44
    fspl = 20 * math.log10(data.distance_km) + 20 * math.log10(data.freq_mhz) + 32.44

    received_power = (
        data.tx_power_dbm
        + data.gain_tx_db
        + data.gain_rx_db
        - data.system_loss_db
        - fspl
    )

    margin = received_power - data.rx_sensitivity_dbm

    return LinkBudgetResult(
        fspl_db=round(fspl, 2),
        received_power_dbm=round(received_power, 2),
        link_margin_db=round(margin, 2),
    )
