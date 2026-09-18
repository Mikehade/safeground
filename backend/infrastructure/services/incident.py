"""
Incident service — anonymous report submission and status checks.

Receipt tokens: a random hex string shown once to the reporter.
We store only the bcrypt hash. No way to enumerate reporters.
"""
import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple

import bcrypt

from infrastructure.repository.incident import IncidentRepository
from infrastructure.services.base import BaseService

from utils.logger import get_logger

logger = get_logger()


class IncidentService(BaseService):

    def __init__(self, incident_repo: IncidentRepository):
        self.incident_repo = incident_repo

    async def submit_report(
        self, data: Dict[str, Any]
    ) -> Tuple[Dict, str]:
        """
        Submit an anonymous incident report.
        Returns (incident_dict, plaintext_token).
        The plaintext token is shown to the user exactly once.
        """
        token = f"SG-{secrets.token_hex(8)}"
        token_hash = bcrypt.hashpw(
            token.encode(), bcrypt.gensalt()
        ).decode()

        incident = await self.incident_repo.create(
            {
                "receipt_token_hash": token_hash,
                "incident_type": data["incident_type"],
                "description": data.get("description"),
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "city": data.get("city"),
                "region": data.get("region"),
                "severity": data.get("severity", 0.5),
            }
        )

        incident_dict = {
            "id": str(incident.id),
            "incident_type": incident.incident_type.value,
            "status": incident.status.value,
            "created_at": incident.created_at.isoformat(),
        }
        return incident_dict, token

    async def check_status(self, token: str) -> Optional[Dict]:
        """Look up incident by plaintext receipt token."""
        # For hackathon: linear scan. Production: store a token prefix index.
        incidents = await self.incident_repo.get_all(limit=5000)
        for inc in incidents:
            if bcrypt.checkpw(token.encode(), inc.receipt_token_hash.encode()):
                return {
                    "id": str(inc.id),
                    "status": inc.status.value,
                    "incident_type": inc.incident_type.value,
                    "created_at": inc.created_at.isoformat(),
                }
        return None

    async def get_recent(
        self, region: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        filters = []
        if region:
            from infrastructure.db.models.incident import Incident

            filters.append(Incident.region == region)

        incidents = await self.incident_repo.get_all(
            limit=limit, filters=filters if filters else None
        )
        return [
            {
                "id": str(inc.id),
                "incident_type": inc.incident_type.value,
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "severity": inc.severity,
                "city": inc.city,
                "created_at": inc.created_at.isoformat(),
            }
            for inc in incidents
        ]
