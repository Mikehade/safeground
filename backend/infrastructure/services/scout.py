"""
Scout service — route safety analysis.

Handles data gathering (routes, corridor incidents). The AI synthesis
happens in the ScoutAgent via LLM tool calls.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.repository.incident import IncidentRepository
from infrastructure.repository.route_assessment import RouteAssessmentRepository
from infrastructure.services.base import BaseService

from utils.logger import get_logger

logger = get_logger()


class ScoutService(BaseService):

    def __init__(
        self,
        incident_repo: IncidentRepository,
        assessment_repo: RouteAssessmentRepository,
    ):
        self.incident_repo = incident_repo
        self.assessment_repo = assessment_repo

    async def get_corridor_incidents(
        self,
        route_geometry: List[Dict],
        buffer_km: float = 0.5,
        hours_back: int = 72,
    ) -> List[Dict]:
        """Find incidents along a route corridor."""
        bbox = self._compute_corridor_bbox(route_geometry, buffer_km)
        incidents = await self.incident_repo.find_in_corridor(
            min_lat=bbox["min_lat"],
            max_lat=bbox["max_lat"],
            min_lng=bbox["min_lng"],
            max_lng=bbox["max_lng"],
            hours_back=hours_back,
        )
        return [
            {
                "type": inc.incident_type.value,
                "lat": inc.latitude,
                "lng": inc.longitude,
                "severity": inc.severity,
                "city": inc.city,
                "hours_ago": self._hours_since(inc.created_at),
                "created_at": inc.created_at.isoformat(),
            }
            for inc in incidents
        ]

    async def cache_assessment(self, data: Dict[str, Any]) -> Dict:
        """Cache a route assessment for future lookups."""
        assessment = await self.assessment_repo.create(data)
        return {"id": str(assessment.id)}

    async def get_cached_assessment(
        self, origin_geohash: str, dest_geohash: str
    ) -> Optional[Dict]:
        assessment = await self.assessment_repo.find_cached(
            origin_geohash, dest_geohash
        )
        if not assessment:
            return None
        return {
            "risk_score": assessment.risk_score,
            "advisory_text": assessment.advisory_text,
            "incidents_summary": assessment.incidents_summary,
            "assessed_at": assessment.created_at.isoformat(),
        }

    @staticmethod
    def _compute_corridor_bbox(
        geometry: List[Dict], buffer_km: float
    ) -> Dict[str, float]:
        lats = [p["lat"] for p in geometry]
        lngs = [p["lng"] for p in geometry]
        buffer_deg = buffer_km * 0.009
        return {
            "min_lat": min(lats) - buffer_deg,
            "max_lat": max(lats) + buffer_deg,
            "min_lng": min(lngs) - buffer_deg,
            "max_lng": max(lngs) + buffer_deg,
        }

    @staticmethod
    def _hours_since(dt: datetime) -> float:
        delta = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
        return round(delta.total_seconds() / 3600, 1)
