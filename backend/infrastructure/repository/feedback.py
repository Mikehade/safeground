"""Anonymous feedback repository."""
from infrastructure.db.models.feedback import Feedback
from infrastructure.repository.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    def __init__(self, session_factory):
        super().__init__(Feedback, session_factory)
