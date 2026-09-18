"""Safety resources API — find nearby shelters, hotlines, legal aid."""
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from infrastructure.config.container import Container

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/nearby")
@inject
async def find_nearby(
    lat: float,
    lng: float,
    resource_type: Optional[str] = None,
    radius_km: float = 10.0,
    resource_service=Depends(Provide[Container.safety_resource_service]),
):
    """Find nearby safety resources."""
    return await resource_service.find_nearby(
        lat, lng, resource_type, radius_km
    )
