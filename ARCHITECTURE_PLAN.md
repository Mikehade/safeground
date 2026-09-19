# SafeGround — Technical Architecture

2026-09-18 · @Someone

## 1. Monorepo Structure

Same monorepo shape you use in Elle — FastAPI backend, React/TS frontend, Docker Compose. No auth layer since we're zero-identity.

```
safeground/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings
│   │   │   ├── privacy.py              # IP stripping, receipt tokens
│   │   │   └── constants/
│   │   │       ├── incident_types.py
│   │   │       ├── model_registry.py
│   │   │       └── risk_scoring.py
│   │   ├── agents/
│   │   │   ├── base.py                 # BaseAgent (llm+tools OR graph)
│   │   │   └── scout_agent.py
│   │   ├── graphs/
│   │   │   └── scout_graph.py
│   │   ├── tools/
│   │   │   ├── base.py                 # BaseTool + ToolRegistry
│   │   │   ├── web_tools.py            # scrape_url, search_content
│   │   │   ├── incident_tools.py
│   │   │   └── routing_tools.py
│   │   └── prompts/
│   │       └── scout.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py                 # Base (UUID pk, timestamps)
│   │   │   ├── session.py              # Database class
│   │   │   └── models/
│   │   │       ├── incident.py
│   │   │       ├── safety_resource.py
│   │   │       ├── route_assessment.py
│   │   │       ├── feedback.py
│   │   │       └── web_intelligence.py
│   │   ├── repository/
│   │   │   ├── base.py                 # BaseRepository ABC
│   │   │   ├── incident.py
│   │   │   ├── safety_resource.py
│   │   │   ├── route_assessment.py
│   │   │   └── feedback.py
│   │   ├── services/
│   │   │   ├── base.py                 # BaseService ABC
│   │   │   ├── incident.py
│   │   │   ├── scout.py
│   │   │   ├── safety_resource.py
│   │   │   └── feedback.py
│   │   ├── language_models/
│   │   │   ├── base.py
│   │   │   └── bedrock.py
│   │   ├── langgraph_models/
│   │   │   ├── base.py
│   │   │   └── bedrock.py
│   │   ├── clients/
│   │   │   ├── firecrawl.py
│   │   │   ├── serp.py
│   │   │   └── mapping.py
│   │   ├── cache/redis/
│   │   ├── middleware/
│   │   │   ├── privacy.py
│   │   │   └── rate_limit.py
│   │   └── config/
│   │       └── container.py
│   ├── api/
│   │   ├── incidents/ (router, schemas)
│   │   ├── scout/     (router, schemas)
│   │   ├── resources/ (router, schemas)
│   │   └── feedback/  (router, schemas)
│   ├── alembic/
│   ├── tests/unit/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/ (Map, Report, Scout, Resources)
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   └── pages/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

Key differences from Elle: no websocket consumers (REST-only), no auth middleware, no user tables.

## 2. Database Layer

### Base model — identical to yours

```python
# infrastructure/db/base.py
import typing as t
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy.dialects.postgresql import UUID

class_registry: t.Dict = {}

@as_declarative(class_registry=class_registry)
class Base:
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                index=True, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), default=None, nullable=True)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
```

### Session — identical to yours

```python
# infrastructure/db/session.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

class Database:
    def __init__(self, db_url: str, **engine_kwargs):
        self._engine = create_async_engine(db_url, **engine_kwargs)
        self._session_factory = async_sessionmaker(
            bind=self._engine, class_=AsyncSession,
            expire_on_commit=False, autoflush=False, autocommit=False,
        )

    @asynccontextmanager
    async def session(self):
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self):
        await self._engine.dispose()
```

### Models — SafeGround-specific

```python
# infrastructure/db/models/incident.py
from sqlalchemy import Column, String, Float, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from infrastructure.db.base import Base
import enum

class IncidentType(str, enum.Enum):
    POLICE_BRUTALITY = "police_brutality"
    CORRUPTION = "corruption"
    GBV = "gbv"
    GANG_ACTIVITY = "gang_activity"
    UNREST = "unrest"
    ROBBERY = "robbery"
    OTHER = "other"

class IncidentStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    ROUTED = "routed"
    RESOLVED = "resolved"

class Incident(Base):
    receipt_token_hash = Column(String(128), nullable=False, index=True)
    incident_type = Column(SAEnum(IncidentType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    city = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    severity = Column(Float, default=0.5)  # 0.0 to 1.0
    status = Column(SAEnum(IncidentStatus), default=IncidentStatus.PENDING)
    metadata_ = Column("metadata", JSONB, default={})
```

```python
# infrastructure/db/models/safety_resource.py
class ResourceType(str, enum.Enum):
    SHELTER = "shelter"
    LEGAL_AID = "legal_aid"
    HOTLINE = "hotline"
    HOSPITAL = "hospital"
    CSO = "cso"  # civil society org
    POLICE_OVERSIGHT = "police_oversight"

class SafetyResource(Base):
    name = Column(String(255), nullable=False)
    resource_type = Column(SAEnum(ResourceType), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    operating_hours = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    metadata_ = Column("metadata", JSONB, default={})
```

```python
# infrastructure/db/models/route_assessment.py (cached)
class RouteAssessment(Base):
    origin_geohash = Column(String(12), nullable=False, index=True)
    dest_geohash = Column(String(12), nullable=False, index=True)
    route_geometry = Column(JSONB, nullable=False)  # GeoJSON
    risk_score = Column(Float, nullable=False)       # 0.0 - 1.0
    advisory_text = Column(Text, nullable=False)
    incidents_summary = Column(JSONB, default={})
    expires_at = Column(DateTime(timezone=True), nullable=False)
```

```python
# infrastructure/db/models/feedback.py
class Feedback(Base):
    assessment_id = Column(UUID(as_uuid=True),
                           ForeignKey("routeassessment.id"), nullable=True)
    helpful = Column(Boolean, nullable=False)
    context = Column(String(500), nullable=True)  # what module they were using
```

```python
# infrastructure/db/models/web_intelligence.py
class WebIntelligenceCache(Base):
    geohash = Column(String(12), nullable=False, index=True)
    data_source = Column(String(100), nullable=False)  # "serp", "firecrawl"
    content_summary = Column(Text, nullable=False)
    threat_level = Column(Float, default=0.0)
    raw_data = Column(JSONB, default={})
    expires_at = Column(DateTime(timezone=True), nullable=False)
```

Notice: no `users` table anywhere. The `receipt_token_hash` on Incident is the only identity link, and it's a one-way bcrypt hash.

## 3. Repository Layer

Abstract base repo so every concrete repo is testable with a mock session factory.

```python
# infrastructure/repository/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(ABC, Generic[ModelType]):
    """Abstract async repository — DI-friendly, testable."""

    def __init__(self, model: Type[ModelType], session_factory):
        self.model = model
        self.session_factory = session_factory

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalars().first()

    async def get_all(
        self, skip: int = 0, limit: int = 100,
        filters: Optional[List] = None
    ) -> List[ModelType]:
        async with self.session_factory() as session:
            query = select(self.model)
            if filters:
                query = query.where(and_(*filters))
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        async with self.session_factory() as session:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            await session.flush()
            await session.refresh(db_obj)
            return db_obj

    async def update_by_id(
        self, id: UUID, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        async with self.session_factory() as session:
            await session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**obj_in)
            )
            return await self.get_by_id(id)

    async def delete_by_id(self, id: UUID) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0
```

### Concrete repos — domain-specific queries

```python
# infrastructure/repository/incident.py
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.sql import text
from infrastructure.db.models.incident import Incident
from infrastructure.repository.base import BaseRepository

class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, session_factory):
        super().__init__(Incident, session_factory)

    async def find_in_corridor(
        self,
        min_lat: float, max_lat: float,
        min_lng: float, max_lng: float,
        hours_back: int = 72,
    ) -> List[Incident]:
        """Find incidents within a bounding box, recent first."""
        async with self.session_factory() as session:
            cutoff = func.now() - text(f"interval '{hours_back} hours'")
            result = await session.execute(
                select(Incident).where(
                    and_(
                        Incident.latitude.between(min_lat, max_lat),
                        Incident.longitude.between(min_lng, max_lng),
                        Incident.created_at >= cutoff,
                        Incident.deleted_at.is_(None),
                    )
                ).order_by(Incident.created_at.desc())
            )
            return result.scalars().all()

    async def get_by_receipt_hash(self, token_hash: str) -> Optional[Incident]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Incident).where(
                    Incident.receipt_token_hash == token_hash
                )
            )
            return result.scalars().first()

    async def get_hotspots(
        self, region: str, limit: int = 20
    ) -> List[dict]:
        """Aggregate incident density by geohash prefix."""
        async with self.session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT city, incident_type,
                           COUNT(*) as count,
                           AVG(severity) as avg_severity
                    FROM incident
                    WHERE region = :region
                      AND deleted_at IS NULL
                      AND created_at >= NOW() - interval '30 days'
                    GROUP BY city, incident_type
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"region": region, "limit": limit}
            )
            return [dict(row._mapping) for row in result]
```

Same pattern for `SafetyResourceRepository`, `RouteAssessmentRepository`, `FeedbackRepository`, `WebIntelligenceCacheRepository` — each extends `BaseRepository[Model]` and adds domain-specific queries.

Every repo takes `session_factory` via DI. In tests you inject a mock or in-memory SQLite factory.

## 4. Service Layer

Services contain business logic and orchestrate repos. Abstract base keeps them testable.

```python
# infrastructure/services/base.py
from abc import ABC
from utils.logger import get_logger

logger = get_logger()

class BaseService(ABC):
    """Base for all services — holds shared concerns."""
    pass
```

### IncidentService

```python
# infrastructure/services/incident.py
import secrets
import bcrypt
from typing import Optional, Dict, Any, Tuple
from infrastructure.services.base import BaseService
from infrastructure.repository.incident import IncidentRepository
from utils.logger import get_logger

logger = get_logger()

class IncidentService(BaseService):
    def __init__(self, incident_repo: IncidentRepository):
        self.incident_repo = incident_repo

    async def submit_report(
        self, data: Dict[str, Any]
    ) -> Tuple[dict, str]:
        """Submit anonymous incident. Returns (incident, plaintext_token)."""
        # Generate receipt token
        token = f"SG-{secrets.token_hex(8)}"
        token_hash = bcrypt.hashpw(
            token.encode(), bcrypt.gensalt()
        ).decode()

        incident = await self.incident_repo.create({
            "receipt_token_hash": token_hash,
            "incident_type": data["incident_type"],
            "description": data.get("description"),
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "city": data.get("city"),
            "region": data.get("region"),
            "severity": data.get("severity", 0.5),
        })
        return incident, token  # token shown to user ONCE

    async def check_status(self, token: str) -> Optional[dict]:
        """Look up incident by plaintext receipt token."""
        # Check against all hashes (or use a prefix index)
        # For hackathon, simple approach:
        incidents = await self.incident_repo.get_all(limit=1000)
        for inc in incidents:
            if bcrypt.checkpw(
                token.encode(), inc.receipt_token_hash.encode()
            ):
                return {
                    "id": str(inc.id),
                    "status": inc.status.value,
                    "incident_type": inc.incident_type.value,
                    "created_at": inc.created_at.isoformat(),
                }
        return None
```

### ScoutService — the core intelligence engine

```python
# infrastructure/services/scout.py
from typing import List, Dict, Any
from infrastructure.services.base import BaseService
from infrastructure.repository.incident import IncidentRepository
from infrastructure.repository.route_assessment import RouteAssessmentRepository
from infrastructure.clients.mapping import MappingClient
from infrastructure.cache.redis.service import CacheService
from utils.logger import get_logger

logger = get_logger()

class ScoutService(BaseService):
    """Route safety analysis — the star of the show."""

    def __init__(
        self,
        incident_repo: IncidentRepository,
        assessment_repo: RouteAssessmentRepository,
        mapping_client: MappingClient,
        cache_service: CacheService,
    ):
        self.incident_repo = incident_repo
        self.assessment_repo = assessment_repo
        self.mapping_client = mapping_client
        self.cache_service = cache_service

    async def get_routes(
        self, origin: Dict, destination: Dict
    ) -> List[Dict[str, Any]]:
        """Get route geometries from mapping API."""
        return await self.mapping_client.get_routes(
            origin_lat=origin["lat"], origin_lng=origin["lng"],
            dest_lat=destination["lat"], dest_lng=destination["lng"],
            alternatives=3,
        )

    async def get_corridor_incidents(
        self, route_geometry: List[Dict],
        buffer_km: float = 0.5, hours_back: int = 72
    ) -> List[Dict]:
        """Find incidents along a route corridor."""
        bbox = self._compute_corridor_bbox(
            route_geometry, buffer_km
        )
        incidents = await self.incident_repo.find_in_corridor(
            min_lat=bbox["min_lat"],
            max_lat=bbox["max_lat"],
            min_lng=bbox["min_lng"],
            max_lng=bbox["max_lng"],
            hours_back=hours_back,
        )
        return [
            {
                "type": inc.incident_type.value,
                "lat": inc.latitude,
                "lng": inc.longitude,
                "severity": inc.severity,
                "hours_ago": self._hours_since(inc.created_at),
            }
            for inc in incidents
        ]

    def _compute_corridor_bbox(
        self, geometry: List[Dict], buffer_km: float
    ) -> Dict[str, float]:
        """Compute bounding box around route polyline."""
        lats = [p["lat"] for p in geometry]
        lngs = [p["lng"] for p in geometry]
        # ~0.009 degrees per km at equator
        buffer_deg = buffer_km * 0.009
        return {
            "min_lat": min(lats) - buffer_deg,
            "max_lat": max(lats) + buffer_deg,
            "min_lng": min(lngs) - buffer_deg,
            "max_lng": max(lngs) + buffer_deg,
        }
```

The ScoutService handles the data gathering. The AI synthesis (turning raw incidents + web data into a human advisory) happens in the agent/tool layer — see section 7.

## 5. LLM Abstraction — Multi-Provider, Dual Path

Same architecture as Elle: `BaseLLMModel` ABC for the direct llm+tools path, `BaseLangGraphModel` ABC for the graph path. Your `BedrockModel` and `LangGraphBedrockModel` copy straight in with minimal trimming.

### What to copy from Elle

- `infrastructure/language_models/base.py` — `BaseLLMModel` ABC with `invoke()`, `prompt()`, `handle_tool_calls()` signatures
- `infrastructure/language_models/bedrock.py` — your full `BedrockModel` with `invoke_with_fallback()`, `_stream_and_assemble()`, the retry chain, everything. SafeGround's agent uses the same `prompt()` → tool loop → yield pattern
- `infrastructure/langgraph_models/base.py` — `BaseLangGraphModel` ABC with `get_chat_model()`, `get_chat_model_chain()`
- `infrastructure/langgraph_models/bedrock.py` — `LangGraphBedrockModel` wrapping `ChatBedrockConverse`
- `core/constants/model_registry.py` — `ModelSpec`, `DEFAULT_BEDROCK_FALLBACK_CHAIN`, `build_attempt_order()`

### What changes

Almost nothing. The only modification is in the agent layer (section 7) where SafeGround's `ScoutAgent` replaces Elle's `StudyPermitApplicationAgent`. The LLM infrastructure is provider-agnostic — if you later add OpenAI, you write `OpenAIModel(BaseLLMModel)` and swap it in the DI container.

### Choosable path — llm+tools vs LangGraph

The agent base class accepts a `use_graph: bool` flag, exactly like your Elle agents:

```python
# app/core/agents/base.py
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

class BaseAgent(ABC):
    """Base agent — picks llm+tools or LangGraph at init."""

    def __init__(
        self,
        llm_model,                # BedrockModel instance
        tool_registry,            # ToolRegistry instance
        prompt_template,          # prompt class
        use_graph: bool = False,
        langgraph_model=None,     # LangGraphBedrockModel (when use_graph=True)
        checkpointer=None,        # LangGraph checkpointer
        **kwargs,
    ):
        self.llm_model = llm_model
        self.tool_registry = tool_registry
        self.prompt_template = prompt_template
        self.use_graph = use_graph
        self.langgraph_model = langgraph_model
        self.checkpointer = checkpointer

        if use_graph:
            self._build_graph()

    def _build_graph(self):
        """Build LangGraph StateGraph. Override in subclass."""
        raise NotImplementedError

    @abstractmethod
    async def run(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run agent — either path."""
        pass

    async def _run_llm_path(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Direct llm + tool loop (your BedrockModel.prompt())."""
        self.llm_model.tool_registry = self.tool_registry
        system = self.prompt_template.render(context)
        async for response in self.llm_model.prompt(
            text=message,
            system_prompt=system,
            message_history=context.get("history", []),
            enable_tools=True,
        ):
            yield response

    async def _run_graph_path(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """LangGraph execution."""
        # Graph invocation — same pattern as your BaseGraphAgent
        pass  # Subclass implements with compiled graph
```

This means during hackathon development you can toggle `use_graph=False` in the DI container for fast iteration, then flip to `True` when you want the graph-based flow for the demo.

## 6. Tool System

Copy `BaseTool` and `ToolRegistry` from Elle verbatim. The pattern — underscore-prefixed methods auto-generate Bedrock `toolSpec` and OpenAI function configs via introspection — is the entire point. SafeGround just adds new tool classes.

### Copy from Elle as-is

- `core/tools/base.py` — `BaseTool` (with `generate_bedrock_config()`, `generate_openai_config()`, `_generate_method_spec()`, `_generate_openai_function_spec()`) and `ToolRegistry`
- `core/tools/web_tools.py` — `WebTools` with `_scrape_url()` and `_search_content()`
- All the scraper/search clients and services they depend on

### New SafeGround tools

```python
# app/core/tools/incident_tools.py
from typing import Any, Dict, List
from app.core.tools.base import BaseTool

class IncidentTools(BaseTool):
    """Tools for querying the incident database."""

    def __init__(
        self, incident_repo, enabled_tools=None, **kwargs
    ):
        super().__init__(enabled_tools=enabled_tools, **kwargs)
        self.incident_repo = incident_repo

    async def execute(self, tool_name, tool_input):
        method = self.get_tool_method(tool_name)
        if not method:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        try:
            tool_input_with_context = {**tool_input, **self.kwargs}
            result = await method(**tool_input_with_context)
            return result if isinstance(result, dict) else {"success": True, "data": result}
        except Exception as e:
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
        - Checking safety of a specific area
        - Analyzing incidents along a route corridor

        Args:
            min_lat: Minimum latitude of bounding box
            max_lat: Maximum latitude of bounding box
            min_lng: Minimum longitude of bounding box
            max_lng: Maximum longitude of bounding box
            hours_back: How many hours back to search

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
                    "created_at": inc.created_at.isoformat(),
                }
                for inc in incidents
            ],
            "count": len(incidents),
        }

    async def _get_area_hotspots(
        self,
        region: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get aggregated incident hotspot data for a region.

        Use this tool when:
        - You need an overview of danger areas in a region
        - Comparing safety between neighborhoods

        Args:
            region: Region name to query (e.g. "Lagos")

        Returns:
            Dictionary with hotspot aggregations
        """
        hotspots = await self.incident_repo.get_hotspots(region)
        return {"success": True, "data": hotspots}
```

```python
# app/core/tools/routing_tools.py
from typing import Any, Dict
from app.core.tools.base import BaseTool

class RoutingTools(BaseTool):
    """Tools for route geometry and geocoding."""

    def __init__(
        self, mapping_client, enabled_tools=None, **kwargs
    ):
        super().__init__(enabled_tools=enabled_tools, **kwargs)
        self.mapping_client = mapping_client

    async def execute(self, tool_name, tool_input):
        method = self.get_tool_method(tool_name)
        if not method:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        try:
            result = await method(**{**tool_input, **self.kwargs})
            return result if isinstance(result, dict) else {"success": True, "data": result}
        except Exception as e:
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
        Get multiple route options between two points.

        Use this tool when:
        - User wants to travel between two locations
        - You need route geometries for safety analysis

        Args:
            origin_lat: Starting latitude
            origin_lng: Starting longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            Dictionary with route geometries and metadata
        """
        routes = await self.mapping_client.get_routes(
            origin_lat, origin_lng, dest_lat, dest_lng,
            alternatives=3,
        )
        return {"success": True, "data": routes}

    async def _geocode_location(
        self,
        location_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Convert a place name to coordinates.

        Use this tool when:
        - User provides a location by name instead of coordinates

        Args:
            location_name: Name of place (e.g. "Lekki Phase 1, Lagos")

        Returns:
            Dictionary with lat/lng coordinates
        """
        result = await self.mapping_client.geocode(location_name)
        return {"success": True, "data": result}
```

### How tools wire to the agent

Just like Elle — `ToolRegistry` combines multiple tool classes, and the agent's `BedrockModel` calls `tool_registry.generate_tool_config()` to get the Bedrock toolSpec, or `generate_openai_functions()` for OpenAI format:

```python
# In the DI container:
scout_tool_registry = ToolRegistry(
    tool_classes=[
        incident_tools,
        routing_tools,
        web_tools,   # scrape_url + search_content from Elle
    ]
)
```

The registry auto-discovers all underscore methods across all tool classes, builds the merged config, and routes execution.

## 7. Agentic Pipeline — Scout Route Safety

This is the hero feature. When a user enters origin + destination, here's the full flow:

### The flow

1. **API receives request** — origin coords, destination coords (or place names)
2. **ScoutAgent.run()** fires — passes the request to the LLM with the tool registry
3. **LLM calls `geocode_location`** (if names given instead of coords)
4. **LLM calls `get_routes`** — gets 2-3 route geometries from mapping API
5. **For each route, LLM calls `query_incidents_in_area`** — bounding box from route corridor
6. **LLM calls `search_content`** — web search for recent news: "unrest Lagos Lekki", "police checkpoint Ikorodu road"
7. **LLM calls `scrape_url`** — if search turns up a relevant article, scrape details
8. **LLM synthesizes** — given all tool results, produces per-route advisory with risk scores

The key insight: the LLM orchestrates the tools, decides which searches to run based on what it finds, and writes the human-readable advisory. You don't hardcode the pipeline — the prompt guides the agent to follow this pattern.

### ScoutAgent implementation

```python
# app/core/agents/scout_agent.py
from typing import Any, AsyncGenerator, Dict
from app.core.agents.base import BaseAgent
from utils.logger import get_logger

logger = get_logger()

class ScoutAgent(BaseAgent):
    """Safety-aware route intelligence agent."""

    def __init__(
        self,
        llm_model,
        tool_registry,
        prompt_template,
        scout_service,      # for caching assessments
        use_graph: bool = False,
        langgraph_model=None,
        checkpointer=None,
        **kwargs,
    ):
        super().__init__(
            llm_model=llm_model,
            tool_registry=tool_registry,
            prompt_template=prompt_template,
            use_graph=use_graph,
            langgraph_model=langgraph_model,
            checkpointer=checkpointer,
            **kwargs,
        )
        self.scout_service = scout_service

    async def run(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if self.use_graph:
            async for resp in self._run_graph_path(message, context, **kwargs):
                yield resp
        else:
            async for resp in self._run_llm_path(message, context, **kwargs):
                yield resp
```

### Scout prompt template

```python
# app/core/prompts/scout.py

SCOUT_SYSTEM_PROMPT = """
You are SafeGround Scout, a safety intelligence agent for communities
in Africa. Your job is to analyze route safety between two locations.

When a user provides an origin and destination:

1. If they gave place names, use geocode_location to get coordinates
2. Use get_routes to get 2-3 alternative routes
3. For EACH route:
   a. Compute a bounding box corridor around the route
   b. Use query_incidents_in_area to check our incident database
   c. Use search_content to search for recent news about safety
      issues along that corridor (e.g. "police brutality [area name]",
      "robbery [area name]", "protest [area name]")
   d. If search results mention specific incidents, use scrape_url
      to get details
4. Synthesize everything into a safety advisory for each route

For each route, provide:
- Route name/description (e.g. "via Third Mainland Bridge")
- Estimated travel time
- Risk level: LOW / MODERATE / HIGH / CRITICAL
- Number and types of incidents found
- Specific hotspots with context (what happened, when, how recent)
- Your recommendation

Consider time of day — a route safe at noon may be dangerous at night.
Consider incident recency — weight recent reports higher.
Consider severity — a robbery report matters more than a traffic report.

Always recommend the safest route, even if it takes longer.
Be specific and actionable — "avoid the stretch between X and Y after
8pm" is better than "this route has some risk."

Respond in the user's language when possible.
"""
```

### Time-of-day awareness

The context dict passed to the agent includes `current_hour` (local time). The prompt instructs the LLM to weight nighttime incidents higher and flag routes that are only dangerous after dark. This comes for free from the LLM's reasoning — no extra logic needed.

## 8. DI Container

Same `dependency_injector` `DeclarativeContainer` pattern as Elle. Everything wired here.

```python
# infrastructure/config/container.py
from dependency_injector import containers, providers
from app.core.config import get_settings
from infrastructure.db.session import Database
from infrastructure.repository.incident import IncidentRepository
from infrastructure.repository.safety_resource import SafetyResourceRepository
from infrastructure.repository.route_assessment import RouteAssessmentRepository
from infrastructure.repository.feedback import FeedbackRepository
from infrastructure.repository.web_intelligence import WebIntelligenceCacheRepository
from infrastructure.services.incident import IncidentService
from infrastructure.services.scout import ScoutService
from infrastructure.services.safety_resource import SafetyResourceService
from infrastructure.services.feedback import FeedbackService
from infrastructure.language_models.bedrock import BedrockModel
from infrastructure.langgraph_models.bedrock import LangGraphBedrockModel
from infrastructure.clients.mapping import MappingClient
from infrastructure.clients.firecrawl import FirecrawlClient
from infrastructure.clients.serp import SerpAPIClient
from infrastructure.cache.redis.client import RedisClient
from infrastructure.cache.redis.manager import RedisCacheManager
from infrastructure.cache.redis.service import CacheService
from infrastructure.services.scraper import ScraperService
from infrastructure.services.search import SearchService
from app.core.tools.base import ToolRegistry
from app.core.tools.web_tools import WebTools
from app.core.tools.incident_tools import IncidentTools
from app.core.tools.routing_tools import RoutingTools
from app.core.agents.scout_agent import ScoutAgent
from app.core.prompts.scout import ScoutPrompt


class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)

    # --- Database ---
    db_engine = providers.Singleton(
        Database,
        providers.Callable(
            lambda cfg: cfg.SQLALCHEMY_DATABASE_URI.replace(
                "postgresql://", "postgresql+asyncpg://"
            ),
            config,
        ),
        pool_size=10,
        max_overflow=5,
        pool_timeout=30,
        pool_recycle=300,
        pool_pre_ping=True,
    )

    # --- Cache ---
    redis_client = providers.Singleton(
        RedisClient,
        url=providers.Callable(lambda c: c.REDIS_URL, config),
    )
    cache_manager = providers.Singleton(RedisCacheManager, client=redis_client)
    cache_service = providers.Singleton(CacheService, manager=cache_manager)

    # --- Clients ---
    serpapi_client = providers.Factory(
        SerpAPIClient,
        api_key=providers.Callable(lambda c: c.SERP_API_KEY, config),
    )
    firecrawl_client = providers.Factory(
        FirecrawlClient,
        api_key=providers.Callable(lambda c: c.FIRECRAWL_API_KEY, config),
    )
    mapping_client = providers.Factory(
        MappingClient,
        api_key=providers.Callable(lambda c: c.MAPPING_API_KEY, config),
    )

    # --- Repositories ---
    incident_repo = providers.Factory(
        IncidentRepository,
        session_factory=db_engine.provided.session,
    )
    safety_resource_repo = providers.Factory(
        SafetyResourceRepository,
        session_factory=db_engine.provided.session,
    )
    route_assessment_repo = providers.Factory(
        RouteAssessmentRepository,
        session_factory=db_engine.provided.session,
    )
    feedback_repo = providers.Factory(
        FeedbackRepository,
        session_factory=db_engine.provided.session,
    )

    # --- Services ---
    scraper_service = providers.Factory(
        ScraperService, scraper_client=firecrawl_client,
    )
    search_service = providers.Factory(
        SearchService, search_client=serpapi_client,
    )
    incident_service = providers.Factory(
        IncidentService, incident_repo=incident_repo,
    )
    scout_service = providers.Factory(
        ScoutService,
        incident_repo=incident_repo,
        assessment_repo=route_assessment_repo,
        mapping_client=mapping_client,
        cache_service=cache_service,
    )
    safety_resource_service = providers.Factory(
        SafetyResourceService,
        resource_repo=safety_resource_repo,
    )
    feedback_service = providers.Factory(
        FeedbackService, feedback_repo=feedback_repo,
    )

    # --- LLM Models ---
    llm_model = providers.Factory(
        BedrockModel,
        aws_access_key=providers.Callable(lambda c: c.AWS_ACCESS_KEY, config),
        aws_secret_key=providers.Callable(lambda c: c.AWS_SECRET_KEY, config),
    )
    langgraph_model = providers.Singleton(
        LangGraphBedrockModel,
        aws_access_key=providers.Callable(lambda c: c.AWS_ACCESS_KEY, config),
        aws_secret_key=providers.Callable(lambda c: c.AWS_SECRET_KEY, config),
    )

    # --- Tools (selective enabling, same as Elle) ---
    incident_tools = providers.Factory(
        IncidentTools,
        incident_repo=incident_repo,
        enabled_tools=["query_incidents_in_area", "get_area_hotspots"],
    )
    routing_tools = providers.Factory(
        RoutingTools,
        mapping_client=mapping_client,
        enabled_tools=["get_routes", "geocode_location"],
    )
    web_tools = providers.Factory(
        WebTools,
        scraper_service=scraper_service,
        search_service=search_service,
        enabled_tools=["scrape_url", "search_content"],
    )

    # --- Tool Registry ---
    scout_tool_registry = providers.Factory(
        ToolRegistry,
        tool_classes=providers.List(
            incident_tools,
            routing_tools,
            web_tools,
        ),
    )

    # --- Prompt ---
    scout_prompt = providers.Factory(ScoutPrompt)

    # --- Agent ---
    scout_agent = providers.Factory(
        ScoutAgent,
        llm_model=llm_model,
        tool_registry=scout_tool_registry,
        prompt_template=scout_prompt,
        scout_service=scout_service,
        use_graph=providers.Callable(lambda c: c.SCOUT_USE_GRAPH, config),
        langgraph_model=langgraph_model,
    )
```

Notice the same patterns as your Elle container: `session_factory=db_engine.provided.session`, selective `enabled_tools` per tool class, `providers.List()` for the registry, and the `use_graph` toggle pulled from config.

## 9. API Layer

### Privacy middleware — the first thing that runs

```python
# infrastructure/middleware/privacy.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class PrivacyMiddleware(BaseHTTPMiddleware):
    """Strip all identifying data before any handler sees it."""

    async def dispatch(self, request: Request, call_next):
        # Overwrite client info so no handler or logger can capture IP
        request.scope["client"] = ("0.0.0.0", 0)
        response = await call_next(request)
        # Strip forwarding headers from response
        for header in ["X-Forwarded-For", "X-Real-IP", "X-Client-IP"]:
            response.headers.pop(header, None)
        return response
```

### Routers

```python
# api/incidents/router.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from api.incidents.schemas import (
    IncidentCreateRequest, IncidentCreateResponse, StatusCheckRequest,
)
from infrastructure.config.container import Container

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.post("/report", response_model=IncidentCreateResponse)
@inject
async def report_incident(
    request: IncidentCreateRequest,
    incident_service=Depends(Provide[Container.incident_service]),
):
    incident, token = await incident_service.submit_report(
        request.model_dump()
    )
    return IncidentCreateResponse(
        receipt_token=token,  # shown to user ONCE
        message="Report submitted. Save your receipt token.",
    )

@router.post("/status")
@inject
async def check_status(
    request: StatusCheckRequest,
    incident_service=Depends(Provide[Container.incident_service]),
):
    result = await incident_service.check_status(request.token)
    if not result:
        return {"found": False, "message": "No report found for this token."}
    return {"found": True, **result}
```

```python
# api/scout/router.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from api.scout.schemas import ScoutRequest, ScoutResponse
from infrastructure.config.container import Container

router = APIRouter(prefix="/scout", tags=["scout"])

@router.post("/analyze", response_model=ScoutResponse)
@inject
async def analyze_route(
    request: ScoutRequest,
    scout_agent=Depends(Provide[Container.scout_agent]),
):
    context = {
        "origin": request.origin.model_dump(),
        "destination": request.destination.model_dump(),
        "current_hour": request.current_hour,
    }

    message = (
        f"Analyze the safety of routes from "
        f"{request.origin.name or request.origin.lat},{request.origin.lng} "
        f"to {request.destination.name or request.destination.lat},{request.destination.lng}. "
        f"Current local time: {request.current_hour}:00."
    )

    result = None
    async for response in scout_agent.run(message, context):
        result = response

    return ScoutResponse(
        advisory=result.get("output", {}).get("message", {}).get("content", []),
        raw_response=result,
    )
```

```python
# api/resources/router.py
@router.get("/nearby")
@inject
async def find_nearby_resources(
    lat: float, lng: float,
    resource_type: Optional[str] = None,
    radius_km: float = 10.0,
    resource_service=Depends(Provide[Container.safety_resource_service]),
):
    return await resource_service.find_nearby(
        lat, lng, resource_type, radius_km
    )
```

```python
# api/feedback/router.py
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
```

### FastAPI app factory

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.middleware.privacy import PrivacyMiddleware
from infrastructure.config.container import Container
from api.incidents.router import router as incidents_router
from api.scout.router import router as scout_router
from api.resources.router import router as resources_router
from api.feedback.router import router as feedback_router

def create_app() -> FastAPI:
    container = Container()
    container.wire(modules=[
        "api.incidents.router",
        "api.scout.router",
        "api.resources.router",
        "api.feedback.router",
    ])

    app = FastAPI(
        title="SafeGround API",
        description="Community safety intelligence platform",
    )

    # Privacy first — before anything else
    app.add_middleware(PrivacyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten for production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(incidents_router, prefix="/api/v1")
    app.include_router(scout_router, prefix="/api/v1")
    app.include_router(resources_router, prefix="/api/v1")
    app.include_router(feedback_router, prefix="/api/v1")

    app.container = container
    return app

app = create_app()
```

No auth on any endpoint. No user context passed. Privacy middleware strips IP before any handler runs.

## 10. Frontend Architecture

React + TypeScript + Vite. Mobile-first. Key libraries:

- **Leaflet.js** (via `react-leaflet`) — map rendering, route polylines, incident markers
- **Zustand** — lightweight state management (no Redux overhead for a hackathon)
- **Axios** or **ky** — API client
- **Tailwind CSS** — rapid styling

### Key components

**Map component** — the centerpiece. Shows the map with route polylines color-coded by risk (green/yellow/red), incident markers with popups showing details, and a panel overlay with the AI advisory text.

**Report form** — minimal: incident type (dropdown), location (tap the map or enter address), optional description, submit. Returns the receipt token in a modal with a "copy" button and a clear message: "Screenshot this. It's the only way to check your report status."

**Scout panel** — origin input, destination input, "Check routes" button. Results show the map with routes and a card per route showing risk level, incident count, and the advisory text. Thumbs up/down buttons on each advisory.

**Resources panel** — location input or "use my location" button. Shows nearby shelters, hotlines, legal aid as a list and on the map. Quick-exit button (a panic button that navigates to a neutral site like Google) — this is critical for GBV users.

### API service layer

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

export const incidentApi = {
  report: (data: IncidentReport) => api.post('/incidents/report', data),
  checkStatus: (token: string) => api.post('/incidents/status', { token }),
};

export const scoutApi = {
  analyze: (data: ScoutRequest) => api.post('/scout/analyze', data),
};

export const resourceApi = {
  findNearby: (lat: number, lng: number, type?: string) =>
    api.get('/resources/nearby', { params: { lat, lng, resource_type: type } }),
};

export const feedbackApi = {
  submit: (data: FeedbackRequest) => api.post('/feedback/', data),
};
```

### State management

```typescript
// store/useScoutStore.ts
import { create } from 'zustand';

interface ScoutState {
  routes: RouteAssessment[];
  loading: boolean;
  error: string | null;
  analyzeRoutes: (origin: Location, dest: Location) => Promise<void>;
  submitFeedback: (assessmentId: string, helpful: boolean) => Promise<void>;
}

export const useScoutStore = create<ScoutState>((set) => ({
  routes: [],
  loading: false,
  error: null,
  analyzeRoutes: async (origin, dest) => {
    set({ loading: true, error: null });
    try {
      const { data } = await scoutApi.analyze({ origin, dest,
        current_hour: new Date().getHours() });
      set({ routes: data.routes, loading: false });
    } catch (e) {
      set({ error: 'Failed to analyze routes', loading: false });
    }
  },
  submitFeedback: async (assessmentId, helpful) => {
    await feedbackApi.submit({ assessment_id: assessmentId, helpful });
  },
}));
```

### Quick-exit button

For GBV and safety users, every screen has a floating "X" button that instantly navigates to Google. No confirmation dialog. The app uses `window.location.replace()` (not `push`) so SafeGround doesn't appear in browser history.

```typescript
const QuickExit = () => (
  <button
    onClick={() => window.location.replace('https://www.google.com')}
    className="fixed top-4 right-4 z-50 bg-gray-200 rounded-full p-3"
    aria-label="Exit quickly"
  >
    ✕
  </button>
);
```

## 11. Build Priority & Hackathon Timeline

Submission closes **21 September 2026**. That's 3 days. Here's the order that maximizes demo impact.

### Day 1 — Foundation + Scout (the hero feature)

- Backend scaffold: FastAPI app factory, Database class, Base model, Alembic init, Docker Compose (Postgres + Redis)
- Copy from Elle: `BaseTool`, `ToolRegistry`, `WebTools`, `BedrockModel`, `LangGraphBedrockModel`, scraper/search clients and services, cache layer, model\_registry constants
- Write SafeGround models + run initial migration
- Build `IncidentRepository`, `IncidentService` (report + status check)
- Build `RoutingTools`, `IncidentTools`
- Wire DI container with all providers
- Build Scout API endpoint — even if the agent returns rough output, the end-to-end flow works
- **Seed the database** with 50-100 realistic incidents across Lagos (Lekki, Ikorodu, Ajah, Victoria Island, Surulere) — this is critical for the demo

### Day 2 — Frontend + Polish the agent

- React scaffold: Vite + TypeScript + Tailwind + react-leaflet
- Map component with route rendering and incident markers
- Scout panel — input form, route cards with risk levels, advisory text
- Report form — incident submission with receipt token display
- Quick-exit button on every screen
- Resources panel — basic lookup by location
- Refine the Scout prompt — test with real queries, tune the advisory quality
- Add feedback (thumbs up/down) on scout results

### Day 3 — Demo artifacts + submission

- Record demo video: walk through reporting an incident, checking a route, seeing the safety advisory, checking status with receipt token
- Write README with clear setup instructions
- Build pitch deck (PDF): problem → personal story → solution → demo screenshots → architecture → scalability → impact
- Write the summary document covering track, sources, trust approach, AI tool usage
- Final testing and cleanup
- Push to public GitHub repo
- Submit

### What to cut if time is tight

- LangGraph path — ship with `use_graph=False`, the llm+tools path works fine
- Resources panel — a nice-to-have, not the demo star
- Web scraping in the agent — hardcode some recent news data in the seed if SerpAPI/Firecrawl setup takes too long
- Feedback persistence — the UI buttons can exist without a backend endpoint initially

### What NOT to cut

- The Scout route analysis flow — this IS the product
- Anonymous incident reporting with receipt tokens — this is the privacy story
- Privacy middleware — judges will ask about this
- Seeded demo data — without incidents in the database, the demo falls flat
- The pitch deck — presentation is 25% of your score
