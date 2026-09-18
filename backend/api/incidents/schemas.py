"""Incident API schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class IncidentCreateRequest(BaseModel):
    incident_type: str = Field(..., description="One of: police_brutality, corruption, gbv, gang_activity, unrest, robbery, electoral, other")
    latitude: float
    longitude: float
    description: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    severity: float = Field(default=0.5, ge=0.0, le=1.0)


class IncidentCreateResponse(BaseModel):
    receipt_token: str
    message: str


class StatusCheckRequest(BaseModel):
    token: str = Field(..., min_length=4, max_length=30)
