"""Safety resources — shelters, hotlines, legal aid, CSOs."""
import enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from infrastructure.db.base import Base


class ResourceType(str, enum.Enum):
    SHELTER = "shelter"
    LEGAL_AID = "legal_aid"
    HOTLINE = "hotline"
    HOSPITAL = "hospital"
    CSO = "cso"
    POLICE_OVERSIGHT = "police_oversight"


class SafetyResource(Base):
    name = Column(String(255), nullable=False)
    resource_type = Column(SAEnum(ResourceType), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    operating_hours = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    metadata_ = Column("metadata", JSONB, default=dict)
