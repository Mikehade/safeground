"""Scout API schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    name: Optional[str] = None


class ScoutRequest(BaseModel):
    origin: LocationInput
    destination: LocationInput
    current_hour: int = Field(default=12, ge=0, le=23)


class ScoutResponse(BaseModel):
    advisory: str
    routes: List[Dict[str, Any]] = []
    tool_calls: int = 0
