"""Anonymous feedback API."""
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from infrastructure.config.container import Container

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    assessment_id: Optional[str] = None
    helpful: bool
    context: Optional[str] = None


@router.post("/")
@inject
async def submit_feedback(
    request: FeedbackRequest,
    feedback_service=Depends(Provide[Container.feedback_service]),
):
    return await feedback_service.submit(
        assessment_id=request.assessment_id,
        helpful=request.helpful,
        context=request.context,
    )
