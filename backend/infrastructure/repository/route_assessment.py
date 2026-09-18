"""Route assessment cache repository."""
from typing import Optional

from sqlalchemy import and_, select, func

from infrastructure.db.models.route_assessment import RouteAssessment
from infrastructure.repository.base import BaseRepository


class RouteAssessmentRepository(BaseRepository[RouteAssessment]):

    def __init__(self, session_factory):
        super().__init__(RouteAssessment, session_factory)

    async def find_cached(
        self, origin_geohash: str, dest_geohash: str
    ) -> Optional[RouteAssessment]:
        """Find a non-expired cached assessment."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(RouteAssessment).where(
                    and_(
                        RouteAssessment.origin_geohash == origin_geohash,
                        RouteAssessment.dest_geohash == dest_geohash,
                        RouteAssessment.expires_at > func.now(),
                    )
                )
            )
            return result.scalars().first()
