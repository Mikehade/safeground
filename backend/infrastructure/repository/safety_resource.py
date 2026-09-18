"""Safety resource repository — nearby lookups."""
from typing import List, Optional

from sqlalchemy import and_, select, text

from infrastructure.db.models.safety_resource import SafetyResource
from infrastructure.repository.base import BaseRepository


class SafetyResourceRepository(BaseRepository[SafetyResource]):

    def __init__(self, session_factory):
        super().__init__(SafetyResource, session_factory)

    async def find_nearby(
        self,
        lat: float,
        lng: float,
        resource_type: Optional[str] = None,
        radius_km: float = 10.0,
        limit: int = 20,
    ) -> List[SafetyResource]:
        """Find resources within radius using bounding-box approximation."""
        buffer_deg = radius_km * 0.009  # ~0.009° per km near equator
        async with self.session_factory() as session:
            filters = [
                SafetyResource.latitude.between(lat - buffer_deg, lat + buffer_deg),
                SafetyResource.longitude.between(lng - buffer_deg, lng + buffer_deg),
                SafetyResource.deleted_at.is_(None),
            ]
            if resource_type:
                filters.append(SafetyResource.resource_type == resource_type)

            result = await session.execute(
                select(SafetyResource)
                .where(and_(*filters))
                .limit(limit)
            )
            return list(result.scalars().all())
