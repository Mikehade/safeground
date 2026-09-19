"""
Scout API — NDJSON streaming with real-time tool progress.

Uses asyncio.Queue so tool events push to the stream in real-time
while the agent runs in a concurrent task.

Stream events (one JSON per line):
  {"type":"status",  "message":"Analyzing routes from A to B..."}
  {"type":"tool",    "name":"search_content", "message":"Searching web: \"...\""}
  {"type":"advisory","text":"# Route Advisory\n...full markdown..."}
  {"type":"done",    "tool_calls":17}
  {"type":"error",   "message":"..."}
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.scout.schemas import ScoutRequest
from infrastructure.config.container import Container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scout", tags=["scout"])

# Sentinel to signal the agent task is done
_DONE = object()


def _ndjson(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n"


def _build_message(request: ScoutRequest):
    o = request.origin
    d = request.destination
    o_desc = o.name or f"{o.lat},{o.lng}"
    d_desc = d.name or f"{d.lat},{d.lng}"
    msg = (
        f"Analyze the safety of routes from {o_desc} to {d_desc}. "
        f"Current local time: {request.current_hour}:00."
    )
    ctx = {
        "origin": o.model_dump(),
        "destination": d.model_dump(),
        "current_hour": request.current_hour,
        "history": [],
    }
    return msg, ctx, o_desc, d_desc


class _ToolEventCollector:
    """
    Wraps tool_registry.execute_tool to push events to an asyncio.Queue
    in real-time as each tool is called — not batched after the fact.
    """

    FRIENDLY = {
        "geocode_location": lambda i: f"Geocoding '{i.get('location_name', '')}'...",
        "get_routes": lambda _: "Fetching route alternatives...",
        "query_incidents_in_area": lambda _: "Querying incident database for this corridor...",
        "get_area_hotspots": lambda i: f"Checking hotspot data for {i.get('region', 'this region')}...",
        "search_content": lambda i: f"Searching web: \"{i.get('query', '')}\"",
        "scrape_url": lambda i: f"Reading: {i.get('url', '')[:70]}...",
    }

    def __init__(self, original_fn, queue: asyncio.Queue):
        self._original = original_fn
        self._queue = queue
        self.count = 0

    async def __call__(self, tool_name: str, tool_input: dict):
        self.count += 1
        fn = self.FRIENDLY.get(tool_name, lambda _: f"Running {tool_name}...")
        event = {"type": "tool", "name": tool_name, "message": fn(tool_input)}

        # Push to queue immediately — the stream generator reads it in real-time
        await self._queue.put(event)

        # Execute the actual tool
        return await self._original(tool_name, tool_input)


async def _run_agent(scout_agent, msg: str, ctx: dict, queue: asyncio.Queue):
    """
    Run the scout agent in a background task.
    Tool events are pushed to the queue by _ToolEventCollector as they happen.
    The final result (or error) is pushed as the last item.
    """
    original_execute = scout_agent.tool_registry.execute_tool
    collector = _ToolEventCollector(original_execute, queue)
    scout_agent.tool_registry.execute_tool = collector

    try:
        result = None
        async for response in scout_agent.run(msg, ctx):
            result = response

        # Extract advisory text
        advisory = ""
        if result:
            content = result.get("output", {}).get("message", {}).get("content", [])
            for block in content:
                if "text" in block:
                    advisory += block["text"]

        await queue.put({
            "type": "advisory",
            "text": advisory or "Unable to analyze routes at this time.",
        })
        await queue.put({
            "type": "done",
            "tool_calls": result.get("toolCallCount", collector.count) if result else 0,
        })

    except Exception as e:
        logger.error(f"Scout agent error: {e}", exc_info=True)
        await queue.put({"type": "error", "message": str(e)})

    finally:
        # Always restore and signal completion
        scout_agent.tool_registry.execute_tool = original_execute
        await queue.put(_DONE)


@router.post("/stream")
@inject
async def stream_scout(
    request: ScoutRequest,
    scout_agent=Depends(Provide[Container.scout_agent]),
):
    """NDJSON streaming — real-time tool progress as the agent works."""
    msg, ctx, o_desc, d_desc = _build_message(request)

    async def generate() -> AsyncGenerator[str, None]:
        yield _ndjson({"type": "status", "message": f"Analyzing routes from {o_desc} to {d_desc}..."})

        queue: asyncio.Queue = asyncio.Queue()

        # Start the agent in a background task
        task = asyncio.create_task(_run_agent(scout_agent, msg, ctx, queue))

        # Read events from the queue as they arrive
        while True:
            event = await queue.get()
            if event is _DONE:
                break
            yield _ndjson(event)

        # Ensure the task is complete (should already be)
        await task

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/analyze")
@inject
async def analyze_route(
    request: ScoutRequest,
    scout_agent=Depends(Provide[Container.scout_agent]),
):
    """Non-streaming fallback."""
    msg, ctx, _, _ = _build_message(request)
    result = None
    async for response in scout_agent.run(msg, ctx):
        result = response
    if not result:
        return {"advisory": "Unable to analyze routes.", "tool_calls": 0}
    advisory = ""
    for block in result.get("output", {}).get("message", {}).get("content", []):
        if "text" in block:
            advisory += block["text"]
    return {"advisory": advisory, "tool_calls": result.get("toolCallCount", 0)}
