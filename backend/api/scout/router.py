"""Scout API — route safety analysis powered by the agentic pipeline."""
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.scout.schemas import ScoutRequest, ScoutResponse
from infrastructure.config.container import Container

router = APIRouter(prefix="/scout", tags=["scout"])


@router.post("/analyze", response_model=ScoutResponse)
@inject
async def analyze_route(
    request: ScoutRequest,
    scout_agent=Depends(Provide[Container.scout_agent]),
):
    """Analyze route safety between two points using the AI agent."""
    origin = request.origin.model_dump()
    destination = request.destination.model_dump()

    # Build the message for the agent
    origin_desc = request.origin.name or f"{origin.get('lat')},{origin.get('lng')}"
    dest_desc = request.destination.name or f"{destination.get('lat')},{destination.get('lng')}"

    message = (
        f"Analyze the safety of routes from {origin_desc} to {dest_desc}. "
        f"Current local time: {request.current_hour}:00."
    )

    context = {
        "origin": origin,
        "destination": destination,
        "current_hour": request.current_hour,
        "history": [],
    }

    result = None
    async for response in scout_agent.run(message, context):
        result = response

    if not result:
        return ScoutResponse(advisory="Unable to analyze routes at this time.")

    # Extract text from Bedrock response
    advisory = ""
    content = result.get("output", {}).get("message", {}).get("content", [])
    for block in content:
        if "text" in block:
            advisory += block["text"]

    return ScoutResponse(
        advisory=advisory,
        tool_calls=result.get("toolCallCount", 0),
    )
