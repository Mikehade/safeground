"""Cached route safety assessments."""
from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from infrastructure.db.base import Base


class RouteAssessment(Base):
    origin_geohash = Column(String(12), nullable=False, index=True)
    dest_geohash = Column(String(12), nullable=False, index=True)
    route_geometry = Column(JSONB, nullable=False)
    risk_score = Column(Float, nullable=False)  # 0.0 – 1.0
    advisory_text = Column(Text, nullable=False)
    incidents_summary = Column(JSONB, default=dict)
    expires_at = Column(DateTime(timezone=True), nullable=False)
