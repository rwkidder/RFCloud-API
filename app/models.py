from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    visibility = Column(String(16), default="private")
    created_at = Column(TIMESTAMP, server_default=func.now())

class TopologyNode(Base):
    __tablename__ = "topology_nodes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False)
    type = Column(String)
    label = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    elev = Column(Float)
    radio_profile = Column(String)


class TopologyLink(Base):
    __tablename__ = "topology_links"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False)
    node_a = Column(Integer, ForeignKey("topology_nodes.id"))
    node_b = Column(Integer, ForeignKey("topology_nodes.id"))
    band_mhz = Column(Float)
    bw_khz = Column(Float)
    modulation = Column(String)
    tx_power_dbm = Column(Float)
    notes = Column(Text)


class RFLinkResult(Base):
    __tablename__ = "rf_link_results"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("topology_links.id"))
    fspl_db = Column(Float)
    received_power_dbm = Column(Float)
    link_margin_db = Column(Float)
    fresnel_clearance_m = Column(Float)
    is_clear = Column(Boolean)
    calculated_at = Column(DateTime, server_default=func.now())
