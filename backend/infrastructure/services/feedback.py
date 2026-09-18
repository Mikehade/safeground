"""Anonymous feedback service."""
from typing import Any, Dict, Optional

from infrastructure.repository.feedback import FeedbackRepository
from infrastructure.services.base import BaseService


class FeedbackService(BaseService):

    def __init__(self, feedback_repo: FeedbackRepository):
        self.feedback_repo = feedback_repo

    async def submit(
        self,
        assessment_id: Optional[str],
        helpful: bool,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        feedback = await self.feedback_repo.create(
            {
                "assessment_id": assessment_id,
                "helpful": helpful,
                "context": context,
            }
        )
        return {"id": str(feedback.id), "recorded": True}
