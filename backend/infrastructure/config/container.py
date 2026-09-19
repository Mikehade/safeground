"""
DI container — wires everything together.
Same dependency_injector DeclarativeContainer pattern as Elle.
"""
from dependency_injector import containers, providers

from app.core.config import get_settings
from app.core.agents.scout_agent import ScoutAgent
from app.core.prompts.scout import ScoutPrompt
from app.core.tools.base import ToolRegistry
from app.core.tools.incident_tools import IncidentTools
from app.core.tools.routing_tools import RoutingTools
from app.core.tools.web_tools import WebTools
from infrastructure.clients.mapping import MappingClient
from infrastructure.db.session import Database

# from infrastructure.services.scraping_bee import ScrapingBeeService
from infrastructure.clients.firecrawl import FirecrawlClient
# from infrastructure.clients.scraper_api import ScraperAPIClient
from infrastructure.services.scraper import ScraperService  
from infrastructure.services.search import SearchService
from infrastructure.clients.serp import SerpAPIClient

from infrastructure.language_models.bedrock import BedrockModel
from infrastructure.repository.feedback import FeedbackRepository
from infrastructure.repository.incident import IncidentRepository
from infrastructure.repository.route_assessment import RouteAssessmentRepository
from infrastructure.repository.safety_resource import SafetyResourceRepository
from infrastructure.services.feedback import FeedbackService
from infrastructure.services.incident import IncidentService
from infrastructure.services.safety_resource import SafetyResourceService
from infrastructure.services.scout import ScoutService


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

    # --- Clients ---
    mapping_client = providers.Factory(
        MappingClient,
        api_key=providers.Callable(lambda c: c.ORS_API_KEY, config),
    )

     # --- Clients ---
    serpapi_client = providers.Factory(
        SerpAPIClient,
        api_key=providers.Callable(lambda cfg: cfg.SERP_API_KEY, config),
    )

    firecrawl_client = providers.Factory(
        FirecrawlClient,
        api_key=providers.Callable(lambda cfg: cfg.FIRECRAWL_API_KEY, config),
    )

    scraper_service = providers.Factory(
        ScraperService,
        # scraper_client=scraper_api_client,
        scraper_client=firecrawl_client,
        # url_scan_client=virus_total_client,
    )

    search_service = providers.Factory(
        SearchService,
        search_client=serpapi_client,
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
    incident_service = providers.Factory(
        IncidentService,
        incident_repo=incident_repo,
    )
    scout_service = providers.Factory(
        ScoutService,
        incident_repo=incident_repo,
        assessment_repo=route_assessment_repo,
    )
    safety_resource_service = providers.Factory(
        SafetyResourceService,
        resource_repo=safety_resource_repo,
    )
    feedback_service = providers.Factory(
        FeedbackService,
        feedback_repo=feedback_repo,
    )

    # --- LLM Model ---
    llm_model = providers.Factory(
        BedrockModel,
        aws_access_key=providers.Callable(lambda c: c.AWS_ACCESS_KEY, config),
        aws_secret_key=providers.Callable(lambda c: c.AWS_SECRET_KEY, config),
        region_name=providers.Callable(lambda c: c.AWS_REGION_NAME, config),
    )

    # --- Tools (selective enabling) ---
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

    # Web tools 
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
            web_tools,  # uncomment when you wire your scrapers
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
    )
