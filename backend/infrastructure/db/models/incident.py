"""Incident report model — the core of anonymous reporting."""
import enum

from sqlalchemy import Column, Enum as SAEnum, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from infrastructure.db.base import Base


class IncidentType(str, enum.Enum):
    POLICE_BRUTALITY = "police_brutality"
    CORRUPTION = "corruption"
    GBV = "gbv"
    GANG_ACTIVITY = "gang_activity"
    UNREST = "unrest"
    ROBBERY = "robbery"
    ELECTORAL = "electoral"
    OTHER = "other"


class IncidentStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    ROUTED = "routed"
    RESOLVED = "resolved"


class Incident(Base):
    """
    Anonymous incident report.
    receipt_token_hash is a one-way bcrypt hash — no way to reverse it.
    No user_id, no IP, no session — zero identity.
    """

    receipt_token_hash = Column(String(128), nullable=False, index=True)
    incident_type = Column(SAEnum(IncidentType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    city = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    severity = Column(Float, default=0.5)  # 0.0 – 1.0
    status = Column(
        SAEnum(IncidentStatus), default=IncidentStatus.PENDING, index=True
    )
    metadata_ = Column("metadata", JSONB, default=dict)
