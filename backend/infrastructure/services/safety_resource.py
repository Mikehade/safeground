"""Safety resource service — nearby lookups for shelters, hotlines, etc."""
import logging
from typing import Dict, List, Optional

from infrastructure.repository.safety_resource import SafetyResourceRepository
from infrastructure.services.base import BaseService

from utils.logger import get_logger

logger = get_logger()


class SafetyResourceService(BaseService):

    def __init__(self, resource_repo: SafetyResourceRepository):
        self.resource_repo = resource_repo

    async def find_nearby(
        self,
        lat: float,
        lng: float,
        resource_type: Optional[str] = None,
        radius_km: float = 10.0,
    ) -> List[Dict]:
        resources = await self.resource_repo.find_nearby(
            lat, lng, resource_type, radius_km
        )
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "type": r.resource_type.value,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "phone": r.phone,
                "address": r.address,
                "operating_hours": r.operating_hours,
            }
            for r in resources
        ]
