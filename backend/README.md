# SafeGround Backend

FastAPI backend for the SafeGround community safety intelligence platform.

The backend provides the REST API, business services, persistence, Scout AI agent, external integrations, privacy middleware, and database infrastructure.

> For full-stack setup and the recommended project commands, see the [root README](../README.md).

---

# Architecture

```text
HTTP Request
     │
     ▼
┌──────────────────────┐
│       FastAPI        │
│      API Routes      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Service Layer     │
│                      │
│ IncidentService      │
│ ScoutService         │
│ SafetyResourceService│
│ FeedbackService      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Repository Layer   │
│                      │
│ IncidentRepository   │
│ RouteAssessmentRepo  │
│ ResourceRepository   │
│ FeedbackRepository   │
└──────────┬───────────┘
           │
           ▼
       PostgreSQL
```

Scout introduces an additional AI execution path:

```text
ScoutService
     │
     ▼
 ScoutAgent
     │
     ├── IncidentTools
     ├── RoutingTools
     ├── WebTools
     │
     ▼
AWS Bedrock / Claude
```

Dependency injection connects the application, services, repositories, database, external clients, and language models.

---

# Directory Structure

```text
backend/
├── Dockerfile
├── requirements.txt
├── main.py
├── seed_data.py
├── alembic.ini
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── api/
│   ├── feedback/
│   │   └── router.py
│   ├── incidents/
│   │   ├── router.py
│   │   └── schemas.py
│   ├── resources/
│   │   └── router.py
│   └── scout/
│       ├── router.py
│       └── schemas.py
│
├── app/
│   └── core/
│       ├── agents/
│       │   ├── base.py
│       │   └── scout_agent.py
│       ├── constants/
│       ├── graphs/
│       ├── prompts/
│       │   └── scout.py
│       └── tools/
│           ├── base.py
│           ├── incident_tools.py
│           ├── routing_tools.py
│           └── web_tools.py
│
├── infrastructure/
│   ├── cache/
│   │   └── redis/
│   ├── clients/
│   │   ├── firecrawl.py
│   │   ├── mapping.py
│   │   ├── scraper.py
│   │   ├── scraper_api.py
│   │   ├── scraping_bee.py
│   │   └── serp.py
│   ├── config/
│   │   └── container.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models/
│   │   └── session.py
│   ├── langgraph_models/
│   ├── language_models/
│   │   ├── base.py
│   │   └── bedrock.py
│   ├── middleware/
│   │   └── privacy.py
│   ├── repository/
│   │   ├── base.py
│   │   ├── feedback.py
│   │   ├── incident.py
│   │   ├── route_assessment.py
│   │   └── safety_resource.py
│   └── services/
│       ├── base.py
│       ├── feedback.py
│       ├── incident.py
│       ├── safety_resource.py
│       ├── scout.py
│       ├── scraper.py
│       └── search.py
│
├── tests/
│   └── unit/
│       ├── agents/
│       ├── repository/
│       ├── services/
│       └── tools/
│
└── utils/
    └── logger.py
```

---

# API Layer

The API layer contains FastAPI routers and request/response schemas.

```text
api/
├── incidents/
├── scout/
├── resources/
└── feedback/
```

## Incidents

Responsible for anonymous safety incident submission and incident-related API operations.

## Scout

Provides the API entry point for safety-aware route analysis.

## Resources

Provides access to safety resources.

## Feedback

Handles application feedback.

Routes should remain thin and delegate business logic to the service layer.

---

# Service Layer

Business logic is implemented in:

```text
infrastructure/services/
```

Current services include:

* `IncidentService`
* `ScoutService`
* `SafetyResourceService`
* `FeedbackService`
* `ScraperService`
* `SearchService`

The service layer coordinates repositories, agents, and external infrastructure without coupling API routes directly to implementation details.

---

# Repository Layer

Repositories encapsulate persistence operations.

```text
infrastructure/repository/
```

Current repositories include:

* `IncidentRepository`
* `RouteAssessmentRepository`
* `SafetyResourceRepository`
* `FeedbackRepository`

A common repository abstraction is provided through:

```text
infrastructure/repository/base.py
```

This keeps database access separate from business logic.

---

# Database

SafeGround uses:

* PostgreSQL
* SQLAlchemy
* async database access
* asyncpg
* Alembic migrations

Database models are located under:

```text
infrastructure/db/models/
```

Current domain models include:

```text
feedback.py
incident.py
route_assessment.py
safety_resource.py
web_intelligence.py
```

Database sessions are managed through:

```text
infrastructure/db/session.py
```

---

# Database Migrations

Apply migrations:

```bash
make db-migrate
```

Create a migration:

```bash
make db-migration MESSAGE="describe the change"
```

Downgrade the latest migration:

```bash
make db-downgrade
```

For direct Alembic usage:

```bash
cd backend
alembic upgrade head
```

---

# Scout Agent

Scout is the AI-powered safety analysis component.

```text
app/core/agents/
├── base.py
└── scout_agent.py
```

The agent is responsible for orchestrating safety analysis rather than directly accessing the database.

A typical flow is:

```text
User Journey
     │
     ▼
Scout API
     │
     ▼
ScoutService
     │
     ▼
ScoutAgent
     │
     ├───────────────┐
     ▼               ▼
Incident Tools    Route Tools
     │               │
     └───────┬───────┘
             ▼
        Web Tools
             │
             ▼
        LLM Reasoning
             │
             ▼
    Safety Recommendation
```

---

# Scout Tools

Tools are located under:

```text
app/core/tools/
```

## IncidentTools

Provides the agent with access to relevant incident information.

## RoutingTools

Provides route-related capabilities.

## WebTools

Provides web search and scraping capabilities.

The tool system is designed to generate provider-specific tool configurations from Python tool definitions and docstrings.

---

# Language Models

Language-model abstractions are located under:

```text
infrastructure/language_models/
```

Current implementation:

```text
base.py
bedrock.py
```

AWS Bedrock provides the production LLM integration.

AWS configuration:

```env
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION_NAME=us-east-1
```

---

# LangGraph

Scout can optionally use a graph-based execution path.

Configuration:

```env
SCOUT_USE_GRAPH=false
```

When enabled:

```env
SCOUT_USE_GRAPH=true
```

The graph-related implementation is located under:

```text
app/core/graphs/
infrastructure/langgraph_models/
```

The exact execution path should be treated as an implementation detail of Scout rather than something API consumers need to know about.

---

# External Clients

External integrations are isolated under:

```text
infrastructure/clients/
```

Current clients include integrations for:

* OpenRouteService
* SerpAPI
* Firecrawl
* ScrapingBee
* Generic scraping
* Mapping

Relevant environment variables:

```env
ORS_API_KEY=
SERP_API_KEY=
FIRECRAWL_API_KEY=
```

---

# Configuration

Application settings are defined using Pydantic Settings.

```text
app/core/config.py
```

Configuration is loaded from:

```text
backend/.env
```

Important settings include:

```env
APP_NAME=SafeGround
DEBUG=true
LOG_LEVEL=INFO

PG_USERNAME=postgres
PG_PASSWORD=postgres
PG_HOSTNAME=localhost
PG_PORT=5432
PG_DB_NAME=safeground

REDIS_URL=redis://localhost:6379/0

AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION_NAME=us-east-1

ORS_API_KEY=
SERP_API_KEY=
FIRECRAWL_API_KEY=

SCOUT_USE_GRAPH=false

RATE_LIMIT_PER_IP=60
RATE_LIMIT_WINDOW=60
```

The PostgreSQL connection string is assembled from the `PG_*` settings.

---

# Dependency Injection

The dependency-injection container is located at:

```text
infrastructure/config/container.py
```

It is responsible for wiring application dependencies such as:

* Database sessions
* Repositories
* Services
* External clients
* Language models
* Agents

This allows services and agents to depend on abstractions rather than constructing infrastructure directly.

---

# Privacy Middleware

Privacy-related request processing is implemented under:

```text
infrastructure/middleware/privacy.py
```

The middleware supports SafeGround's privacy-first design by removing request information that should not be passed further into application processing.

SafeGround does not require a user account for incident reporting.

Receipt tokens are designed to provide a way to retrieve report status without creating a conventional user identity.

---

# Running the Backend

From the repository root:

```bash
make start-backend
```

View logs:

```bash
make logs-backend
```

Open a shell:

```bash
make shell-backend
```

For local development:

```bash
make setup-backend
make run-backend-local
```

The API is available at:

```text
http://localhost:8000
```

---

# API Documentation

When running in development, FastAPI's generated documentation is available at:

```text
http://localhost:8000/docs
```

The exact available routes should be treated as the source of truth in the FastAPI routers.

---

# Testing

Tests are located under:

```text
tests/
```

Run all tests:

```bash
make test
```

Run with coverage:

```bash
make test-cov
```

Backend unit tests are organized by:

```text
tests/unit/
├── agents/
├── repository/
├── services/
└── tools/
```

The architecture is intentionally designed so service, repository, agent, and tool logic can be tested independently.

---

# Development Guidelines

### Keep routers thin

Do not place business logic directly in API route handlers.

### Keep database access in repositories

Services and agents should not contain raw persistence logic.

### Keep external integrations in infrastructure

API keys, SDK clients, HTTP clients, and third-party integrations belong under infrastructure.

### Agents use tools

Agents should access application capabilities through tools rather than directly reaching into repositories or database sessions.

### Prefer dependency injection

Dependencies should be provided by the application container rather than manually instantiated throughout the codebase.

---

# Backend Commands

Most commands should be executed from the repository root.

```bash
make start-backend
make stop-backend
make build-backend
make logs-backend
make shell-backend

make db-migrate
make db-migration MESSAGE="migration message"
make db-downgrade

make test
make test-cov

make format
make lint
```

See the root [`README.md`](../README.md) for the complete project-level Makefile reference.

---

# Related Documentation

* [`../README.md`](../README.md) — full-stack setup and project commands
* [`../frontend/README.md`](../frontend/README.md) — frontend architecture and development
