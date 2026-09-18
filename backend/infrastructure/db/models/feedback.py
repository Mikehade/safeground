"""Anonymous feedback on route assessments."""
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from infrastructure.db.base import Base


class Feedback(Base):
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("routeassessment.id"),
        nullable=True,
        index=True,
    )
    helpful = Column(Boolean, nullable=False)
    context = Column(String(500), nullable=True)
