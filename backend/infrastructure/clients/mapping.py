"""
Mapping client — OpenRouteService for routes, Nominatim for geocoding.
Both are free/open-source. No API key needed for Nominatim.
OpenRouteService free tier: 2000 reqs/day.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from utils.logger import get_logger

logger = get_logger()

ORS_BASE = "https://api.openrouteservice.org"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"


class MappingClient:

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {
            "User-Agent": "SafeGround/1.0",
        }
        if api_key:
            self.headers["Authorization"] = api_key

    async def get_routes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        alternatives: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get route alternatives between two points."""
        if not self.api_key:
            # Fallback: return a simple straight-line "route"
            return self._fallback_routes(
                origin_lat, origin_lng, dest_lat, dest_lng
            )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{ORS_BASE}/v2/directions/driving-car/geojson",
                    headers=self.headers,
                    json={
                        "coordinates": [
                            [origin_lng, origin_lat],
                            [dest_lng, dest_lat],
                        ],
                        "alternative_routes": {
                            "target_count": alternatives,
                            "share_factor": 0.6,
                            "weight_factor": 1.6,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                routes = []
                for i, feature in enumerate(data.get("features", [])):
                    props = feature.get("properties", {})
                    summary = props.get("summary", {})
                    coords = feature["geometry"]["coordinates"]
                    routes.append(
                        {
                            "index": i,
                            "distance_km": round(
                                summary.get("distance", 0) / 1000, 1
                            ),
                            "duration_min": round(
                                summary.get("duration", 0) / 60, 0
                            ),
                            "geometry": [
                                {"lat": c[1], "lng": c[0]} for c in coords
                            ],
                        }
                    )
                return routes

            except Exception as e:
                logger.error(f"ORS routing failed: {e}", exc_info=True)
                return self._fallback_routes(
                    origin_lat, origin_lng, dest_lat, dest_lng
                )

    async def geocode(self, location_name: str) -> Dict[str, Any]:
        """Geocode a place name to coordinates using Nominatim."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"{NOMINATIM_BASE}/search",
                    headers=self.headers,
                    params={
                        "q": location_name,
                        "format": "json",
                        "limit": 1,
                    },
                )
                resp.raise_for_status()
                results = resp.json()

                if not results:
                    return {
                        "found": False,
                        "message": f"Could not find '{location_name}'",
                    }

                place = results[0]
                return {
                    "found": True,
                    "lat": float(place["lat"]),
                    "lng": float(place["lon"]),
                    "display_name": place.get("display_name", location_name),
                }

            except Exception as e:
                logger.error(f"Geocoding failed: {e}", exc_info=True)
                return {"found": False, "message": str(e)}

    @staticmethod
    def _fallback_routes(
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> List[Dict]:
        """Simple straight-line route for when ORS is unavailable."""
        mid_lat = (origin_lat + dest_lat) / 2
        mid_lng = (origin_lng + dest_lng) / 2
        return [
            {
                "index": 0,
                "distance_km": 0,
                "duration_min": 0,
                "geometry": [
                    {"lat": origin_lat, "lng": origin_lng},
                    {"lat": mid_lat, "lng": mid_lng},
                    {"lat": dest_lat, "lng": dest_lng},
                ],
            }
        ]
