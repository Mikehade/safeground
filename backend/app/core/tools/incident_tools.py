"""Incident query tools for the Scout agent."""
import logging
from typing import Any, Dict

from app.core.tools.base import BaseTool

from utils.logger import get_logger

logger = get_logger()


class IncidentTools(BaseTool):
    """Tools for querying the incident database."""

    def __init__(self, incident_repo, enabled_tools=None, **kwargs):
        super().__init__(enabled_tools=enabled_tools, **kwargs)
        self.incident_repo = incident_repo

    async def execute(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        method = self.get_tool_method(tool_name)
        if not method:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        try:
            result = await method(**{**tool_input, **self.kwargs})
            return result if isinstance(result, dict) else {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _query_incidents_in_area(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        hours_back: int = 72,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Query reported incidents within a geographic bounding box.

        Use this tool when:
        - Checking safety of a specific area or route corridor
        - Analyzing incident density along a route

        Args:
            min_lat: Southern boundary latitude
            max_lat: Northern boundary latitude
            min_lng: Western boundary longitude
            max_lng: Eastern boundary longitude
            hours_back: How many hours of history to search

        Returns:
            Dictionary with incident data for the area
        """
        incidents = await self.incident_repo.find_in_corridor(
            min_lat, max_lat, min_lng, max_lng, hours_back
        )
        return {
            "success": True,
            "data": [
                {
                    "type": inc.incident_type.value,
                    "lat": inc.latitude,
                    "lng": inc.longitude,
                    "severity": inc.severity,
                    "city": inc.city,
                    "created_at": inc.created_at.isoformat(),
                }
                for inc in incidents
            ],
            "count": len(incidents),
        }

    async def _get_area_hotspots(
        self, region: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Get aggregated incident hotspot data for a region.

        Use this tool when:
        - You need an overview of dangerous areas in a region
        - Comparing safety between neighborhoods

        Args:
            region: Region name (e.g. "Lagos")

        Returns:
            Dictionary with hotspot aggregations by area and type
        """
        hotspots = await self.incident_repo.get_hotspots(region)
        return {"success": True, "data": hotspots}
