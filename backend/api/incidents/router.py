"""Incident API — anonymous reporting and status checks."""
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.incidents.schemas import (
    IncidentCreateRequest,
    IncidentCreateResponse,
    StatusCheckRequest,
)
from infrastructure.config.container import Container

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/report", response_model=IncidentCreateResponse)
@inject
async def report_incident(
    request: IncidentCreateRequest,
    incident_service=Depends(Provide[Container.incident_service]),
):
    """Submit an anonymous incident report. Returns a one-time receipt token."""
    _, token = await incident_service.submit_report(request.model_dump())
    return IncidentCreateResponse(
        receipt_token=token,
        message="Report submitted. Save your receipt token — it cannot be recovered.",
    )


@router.post("/status")
@inject
async def check_status(
    request: StatusCheckRequest,
    incident_service=Depends(Provide[Container.incident_service]),
):
    """Check report status using your receipt token."""
    result = await incident_service.check_status(request.token)
    if not result:
        return {"found": False, "message": "No report found for this token."}
    return {"found": True, **result}


@router.get("/recent")
@inject
async def get_recent_incidents(
    region: str = None,
    limit: int = 50,
    incident_service=Depends(Provide[Container.incident_service]),
):
    """Get recent incidents (public, anonymized)."""
    return await incident_service.get_recent(region=region, limit=limit)
