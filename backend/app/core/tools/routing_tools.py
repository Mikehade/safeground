"""Routing tools — route geometries and geocoding."""
import logging
from typing import Any, Dict

from app.core.tools.base import BaseTool

from utils.logger import get_logger

logger = get_logger()


class RoutingTools(BaseTool):
    """Tools for route geometry and geocoding."""

    def __init__(self, mapping_client, enabled_tools=None, **kwargs):
        super().__init__(enabled_tools=enabled_tools, **kwargs)
        self.mapping_client = mapping_client

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

    async def _get_routes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get multiple route options between two points with geometry.

        Use this tool when:
        - User wants to travel between two locations
        - You need route geometries for corridor safety analysis

        Args:
            origin_lat: Starting point latitude
            origin_lng: Starting point longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            Dictionary with route geometries, distances, and durations
        """
        routes = await self.mapping_client.get_routes(
            origin_lat, origin_lng, dest_lat, dest_lng
        )
        return {"success": True, "data": routes}

    async def _geocode_location(
        self, location_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Convert a place name to latitude/longitude coordinates.

        Use this tool when:
        - User provides a location by name instead of coordinates
        - You need to resolve an area name to coordinates for queries

        Args:
            location_name: Place name (e.g. "Lekki Phase 1, Lagos")

        Returns:
            Dictionary with lat/lng coordinates and formatted address
        """
        result = await self.mapping_client.geocode(location_name)
        return {"success": True, "data": result}
