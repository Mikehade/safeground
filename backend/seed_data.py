"""
Seed the database with realistic incident and resource data for demo.
Run: python seed_data.py
"""
import asyncio
import random
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt

from app.core.config import get_settings
from infrastructure.db.session import Database
from infrastructure.db.models.incident import Incident, IncidentType, IncidentStatus
from infrastructure.db.models.safety_resource import SafetyResource, ResourceType

settings = get_settings()
db_url = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+asyncpg://")

# Lagos neighborhoods with approximate coords
LAGOS_AREAS = [
    {"city": "Lekki Phase 1", "region": "Lagos", "lat": 6.4389, "lng": 3.4728},
    {"city": "Ikorodu", "region": "Lagos", "lat": 6.6194, "lng": 3.5105},
    {"city": "Ajah", "region": "Lagos", "lat": 6.4667, "lng": 3.5833},
    {"city": "Surulere", "region": "Lagos", "lat": 6.4969, "lng": 3.3481},
    {"city": "Victoria Island", "region": "Lagos", "lat": 6.4281, "lng": 3.4219},
    {"city": "Ikeja", "region": "Lagos", "lat": 6.6018, "lng": 3.3515},
    {"city": "Oshodi", "region": "Lagos", "lat": 6.5569, "lng": 3.3414},
    {"city": "Mushin", "region": "Lagos", "lat": 6.5355, "lng": 3.3517},
    {"city": "Yaba", "region": "Lagos", "lat": 6.5095, "lng": 3.3711},
    {"city": "Agege", "region": "Lagos", "lat": 6.6204, "lng": 3.3280},
    {"city": "Maryland", "region": "Lagos", "lat": 6.5742, "lng": 3.3653},
    {"city": "Ojota", "region": "Lagos", "lat": 6.5856, "lng": 3.3810},
    {"city": "Festac Town", "region": "Lagos", "lat": 6.4663, "lng": 3.2839},
    {"city": "Apapa", "region": "Lagos", "lat": 6.4488, "lng": 3.3590},
    {"city": "Badagry", "region": "Lagos", "lat": 6.4153, "lng": 2.8812},
]

INCIDENT_DESCRIPTIONS = {
    IncidentType.POLICE_BRUTALITY: [
        "Officers stopped vehicles and demanded bribes at checkpoint. Those who refused were detained.",
        "Plainclothes officers harassed young men for carrying laptops, demanding to see proof of purchase.",
        "SARS-style checkpoint on this road. Multiple reports of phones being seized.",
        "Police beat a commercial driver who refused to pay. Witnesses were threatened.",
    ],
    IncidentType.ROBBERY: [
        "Armed robbery around 9pm. Two attackers on motorcycle targeting pedestrians.",
        "Multiple car break-ins reported in this area overnight.",
        "Phone snatching hotspot, especially after dark. Multiple incidents this week.",
        "One-chance bus operation reported on this route. Passengers robbed.",
    ],
    IncidentType.GANG_ACTIVITY: [
        "Area boys controlling access to the market. Demanding tolls from traders.",
        "Cult clash in the area. Residents advised to avoid after dark.",
        "Gang confrontation near the junction. Stones and bottles thrown.",
    ],
    IncidentType.UNREST: [
        "Protest blocking the highway. Traffic diverted through side streets.",
        "Demonstration at government building. Heavy police presence, tear gas deployed.",
        "Community protest over power outage entering third day. Road blocked.",
    ],
    IncidentType.CORRUPTION: [
        "Officials at local government office demanding unofficial payments for document processing.",
        "Building permits being withheld unless 'facilitation fee' is paid.",
    ],
    IncidentType.GBV: [
        "Harassment of women reported near the bus stop in the evening.",
        "Multiple reports of stalking in this area. Women advised to travel in groups.",
    ],
}


def jitter(lat: float, lng: float, km: float = 1.0) -> tuple:
    """Add random offset to coordinates within ~km radius."""
    deg = km * 0.009
    return (
        lat + random.uniform(-deg, deg),
        lng + random.uniform(-deg, deg),
    )


async def seed():
    db = Database(db_url, pool_size=5, pool_pre_ping=True)

    # --- Seed incidents ---
    print("Seeding incidents...")
    now = datetime.now(timezone.utc)

    async with db.session() as session:
        for i in range(80):
            area = random.choice(LAGOS_AREAS)
            inc_type = random.choice(list(IncidentType))
            if inc_type == IncidentType.ELECTORAL:
                inc_type = IncidentType.CORRUPTION  # skip electoral for demo density

            descriptions = INCIDENT_DESCRIPTIONS.get(inc_type, ["Incident reported in the area."])
            lat, lng = jitter(area["lat"], area["lng"], km=0.8)

            token = f"SG-{secrets.token_hex(8)}"
            token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()

            hours_ago = random.choice([1, 3, 6, 12, 24, 48, 72, 120, 240])
            created = now - timedelta(hours=hours_ago)

            incident = Incident(
                receipt_token_hash=token_hash,
                incident_type=inc_type,
                description=random.choice(descriptions),
                latitude=round(lat, 6),
                longitude=round(lng, 6),
                city=area["city"],
                region=area["region"],
                severity=round(random.uniform(0.3, 0.95), 2),
                status=random.choice([IncidentStatus.PENDING, IncidentStatus.VERIFIED]),
                created_at=created,
            )
            session.add(incident)

        print(f"  Added 80 incidents across {len(LAGOS_AREAS)} areas")

    # --- Seed safety resources ---
    print("Seeding safety resources...")
    resources_data = [
        {"name": "DSVRT Lagos (GBV Hotline)", "resource_type": ResourceType.HOTLINE,
         "latitude": 6.4355, "longitude": 3.4106, "phone": "08000333333",
         "address": "Lagos State, Nigeria", "region": "Lagos",
         "operating_hours": "24/7"},
        {"name": "Mirabel Centre (Sexual Assault Referral)", "resource_type": ResourceType.SHELTER,
         "latitude": 6.4460, "longitude": 3.3985, "phone": "08000333333",
         "address": "Lagos State University Teaching Hospital, Ikeja", "region": "Lagos",
         "operating_hours": "24/7"},
        {"name": "FIDA Nigeria (Legal Aid for Women)", "resource_type": ResourceType.LEGAL_AID,
         "latitude": 6.4541, "longitude": 3.4198, "phone": "+234-1-7640767",
         "address": "Victoria Island, Lagos", "region": "Lagos",
         "operating_hours": "Mon-Fri 9am-5pm"},
        {"name": "Lagos State Emergency Management Agency", "resource_type": ResourceType.CSO,
         "latitude": 6.5885, "longitude": 3.3634, "phone": "112",
         "address": "Alausa, Ikeja", "region": "Lagos",
         "operating_hours": "24/7"},
        {"name": "Lagos General Hospital", "resource_type": ResourceType.HOSPITAL,
         "latitude": 6.4515, "longitude": 3.3932, "phone": "+234-1-2600090",
         "address": "Marina, Lagos Island", "region": "Lagos",
         "operating_hours": "24/7"},
        {"name": "National Human Rights Commission (Lagos)", "resource_type": ResourceType.POLICE_OVERSIGHT,
         "latitude": 6.4312, "longitude": 3.4215, "phone": "+234-9-6723298",
         "address": "Victoria Island, Lagos", "region": "Lagos",
         "operating_hours": "Mon-Fri 8am-4pm"},
        {"name": "CLEEN Foundation", "resource_type": ResourceType.CSO,
         "latitude": 6.4352, "longitude": 3.4189, "phone": "+234-1-4620211",
         "address": "Victoria Island, Lagos", "region": "Lagos",
         "operating_hours": "Mon-Fri 9am-5pm"},
        {"name": "Women at Risk International Foundation", "resource_type": ResourceType.SHELTER,
         "latitude": 6.5982, "longitude": 3.3450, "phone": "+234-1-7919080",
         "address": "Ikeja, Lagos", "region": "Lagos",
         "operating_hours": "Mon-Sat 8am-6pm"},
    ]

    async with db.session() as session:
        for r_data in resources_data:
            resource = SafetyResource(
                verified_at=now,
                **r_data,
            )
            session.add(resource)
        print(f"  Added {len(resources_data)} safety resources")

    await db.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
