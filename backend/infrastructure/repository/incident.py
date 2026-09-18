"""Incident repository — corridor queries, hotspot aggregation."""
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select, text

from infrastructure.db.models.incident import Incident
from infrastructure.repository.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):

    def __init__(self, session_factory):
        super().__init__(Incident, session_factory)

    async def find_in_corridor(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        hours_back: int = 72,
    ) -> List[Incident]:
        """Find incidents within a bounding box, most recent first."""
        async with self.session_factory() as session:
            cutoff = func.now() - text(f"interval '{hours_back} hours'")
            result = await session.execute(
                select(Incident)
                .where(
                    and_(
                        Incident.latitude.between(min_lat, max_lat),
                        Incident.longitude.between(min_lng, max_lng),
                        Incident.created_at >= cutoff,
                        Incident.deleted_at.is_(None),
                    )
                )
                .order_by(Incident.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_by_receipt_hash(self, token_hash: str) -> Optional[Incident]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Incident).where(
                    Incident.receipt_token_hash == token_hash
                )
            )
            return result.scalars().first()

    async def get_hotspots(
        self, region: str, limit: int = 20
    ) -> List[Dict]:
        """Aggregate incident density by city and type."""
        async with self.session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT city, incident_type,
                           COUNT(*)       AS count,
                           AVG(severity)  AS avg_severity
                    FROM   incident
                    WHERE  region = :region
                      AND  deleted_at IS NULL
                      AND  created_at >= NOW() - interval '30 days'
                    GROUP  BY city, incident_type
                    ORDER  BY count DESC
                    LIMIT  :limit
                """),
                {"region": region, "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    async def count_by_region(self, region: str) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(Incident.id)).where(
                    and_(
                        Incident.region == region,
                        Incident.deleted_at.is_(None),
                    )
                )
            )
            return result.scalar() or 0
