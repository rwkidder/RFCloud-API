from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ---------- PROJECT ----------
class ProjectBase(BaseModel):
    owner: str
    name: str
    visibility: Optional[str] = "private"

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ---------- NODE ----------
class NodeBase(BaseModel):
    project_id: int
    type: Optional[str] = None
    label: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    elev: Optional[float] = None
    radio_profile: Optional[str] = None

class NodeCreate(NodeBase):
    pass

class Node(NodeBase):
    id: int
    class Config:
        orm_mode = True

from pydantic import BaseModel
from datetime import datetime

class RFLinkTestBase(BaseModel):
    tx_node_id: int
    rx_node_id: int
    freq_mhz: float
    distance_km: float | None = None
    fspl_db: float | None = None
    received_power_dbm: float | None = None
    link_margin_db: float | None = None
    fresnel_clearance_m: float | None = None
    is_clear: bool | None = None

class RFLinkTestCreate(RFLinkTestBase):
    pass

class RFLinkTest(RFLinkTestBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True  # replaces orm_mode

