"""Cached web intelligence data for locations."""
from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from infrastructure.db.base import Base


class WebIntelligenceCache(Base):
    geohash = Column(String(12), nullable=False, index=True)
    data_source = Column(String(100), nullable=False)
    content_summary = Column(Text, nullable=False)
    threat_level = Column(Float, default=0.0)
    raw_data = Column(JSONB, default=dict)
    expires_at = Column(DateTime(timezone=True), nullable=False)
