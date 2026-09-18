# SafeGround

**Community safety intelligence platform — zero identity, zero tracking.**

SafeGround helps people in African communities navigate safety risks through anonymous incident reporting, AI-powered route safety analysis, and a verified safety-resource directory.

Built for the **OSF Hackathon 2026 — Track 3: Safety, Reporting & Protection**.

---

## Overview

SafeGround provides three core capabilities:

### 🛡️ Scout — Safety-aware routing

Scout analyzes a journey using available route information, historical incident data, and web intelligence. Its AI agent evaluates potential safety concerns and produces a human-readable safety advisory with hotspot warnings, time-aware considerations, and practical guidance.

### 📢 Report — Anonymous incident reporting

Users can submit safety incidents without creating an account.

SafeGround is designed to avoid storing identifying information. Reports are associated with a one-time receipt token that allows the reporter to check the status of their submission.

Supported incident categories include:

* Police brutality
* Corruption
* Gender-based violence
* Gang activity
* Other community safety incidents

### 🆘 Resources — Safety directory

Users can find safety-related resources such as:

* Shelters
* Hotlines
* Legal aid
* Civil society organizations
* Other verified safety services

The interface also provides a quick-exit mechanism for users who need to leave the application quickly.

---

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│              React / TypeScript / Vite              │
│        Tailwind · Zustand · Axios · Leaflet         │
└───────────────────────┬─────────────────────────────┘
                        │ REST API
                        ▼
┌─────────────────────────────────────────────────────┐
│                    FastAPI API                       │
│                                                     │
│  /incidents   /scout   /resources   /feedback       │
│                       │                             │
│                Service Layer                        │
│                       │                             │
│              Repository Layer                       │
│                       │                             │
│       ┌───────────────┴────────────────┐            │
│       │                                │            │
│ PostgreSQL                         Scout Agent      │
│       │                                │            │
│       │                     ┌──────────┼─────────┐  │
│       │                     │          │         │  │
│       │                  Incidents  Routing   Web    │
│       │                              Tools     Tools  │
│       │                                           │  │
│       │                                      Bedrock │
│       │                                       Claude │
│       └─────────────────────────────────────────────┘
│                                                     │
│                 Redis · DI Container                │
└─────────────────────────────────────────────────────┘
```

### Backend layers

```text
API
 ↓
Services
 ↓
Repositories
 ↓
PostgreSQL
```

AI-specific orchestration is kept in the agent/tool layer rather than placing database access directly inside the agent.

The backend uses dependency injection to compose application services and infrastructure dependencies.

---

## Repository Structure

```text
.
├── README.md
├── Makefile
├── docker-compose.yml
│
├── backend/
│   ├── README.md
│   ├── Dockerfile
│   ├── alembic/
│   ├── api/
│   ├── app/
│   ├── infrastructure/
│   ├── tests/
│   ├── utils/
│   ├── main.py
│   ├── requirements.txt
│   └── seed_data.py
│
└── frontend/
    ├── README.md
    ├── Dockerfile
    ├── src/
    ├── public/
    ├── package.json
    └── vite.config.ts
```

For detailed implementation documentation:

* **Backend:** [`backend/README.md`](./backend/README.md)
* **Frontend:** [`frontend/README.md`](./frontend/README.md)

---

# Prerequisites

For the recommended Docker-based workflow:

| Tool           | Version | Purpose                   |
| -------------- | ------: | ------------------------- |
| Docker         |     24+ | Container runtime         |
| Docker Compose |     v2+ | Full-stack orchestration  |
| GNU Make       |   3.81+ | Project command interface |

For local development without containers:

| Tool       | Version |
| ---------- | ------: |
| Python     |   3.12+ |
| Node.js    |     20+ |
| PostgreSQL |     16+ |
| Redis      |      7+ |

AWS Bedrock access is required for Scout's LLM functionality.

---

# Quick Start

The **root Makefile is the primary command interface for SafeGround**.

You normally do not need to run Docker Compose, Uvicorn, or npm commands manually.

## 1. Clone

```bash
git clone git@github.com:Mikehade/safeground.git
cd safeground
```

## 2. Configure the backend

Create the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Then configure the required credentials and service settings.

If `.env.example` is not present, create `backend/.env` manually using the environment variables documented below.

## 3. Start SafeGround

```bash
make start
```

This starts the full application stack:

```text
PostgreSQL
Redis
   ↓
Backend API
   ↓
Frontend
```

---

# Application URLs

When running the Docker development stack:

| Service           | URL                        |
| ----------------- | -------------------------- |
| Frontend          | http://localhost:5173      |
| Backend API       | http://localhost:8000      |
| API documentation | http://localhost:8000/docs |

---

# Makefile Reference

Run:

```bash
make help
```

to see the available commands.

## Full Stack

| Command        | Description                                |
| -------------- | ------------------------------------------ |
| `make start`   | Start the complete application stack       |
| `make stop`    | Stop the application stack                 |
| `make restart` | Restart the application stack              |
| `make build`   | Build all Docker images                    |
| `make rebuild` | Rebuild all images without using the cache |
| `make logs`    | Follow logs from all services              |
| `make ps`      | Show running services                      |

### Typical workflow

```bash
make start
make logs
make ps
```

Stop everything with:

```bash
make stop
```

---

# Backend Commands

The root Makefile also provides backend-specific commands.

```bash
make start-backend
make stop-backend
make build-backend
make logs-backend
make shell-backend
```

These are useful when developing the API without needing to work with the frontend container.

See [`backend/README.md`](./backend/README.md) for backend-specific architecture, migrations, testing, and development details.

---

# Frontend Commands

```bash
make start-frontend
make stop-frontend
make build-frontend
make logs-frontend
make shell-frontend
```

See [`frontend/README.md`](./frontend/README.md) for frontend-specific development and architecture documentation.

---

# Database Commands

SafeGround uses PostgreSQL.

Start PostgreSQL:

```bash
make start-db
```

Stop PostgreSQL:

```bash
make stop-db
```

Open a PostgreSQL shell:

```bash
make db-shell
```

Apply existing migrations:

```bash
make db-migrate
```

Create a new migration:

```bash
make db-migration MESSAGE="add new incident field"
```

Downgrade the latest migration:

```bash
make db-downgrade
```

> `db-reset` is destructive and should only be used when resetting local development data is intentional.

---

# Redis Commands

Start Redis:

```bash
make start-redis
```

Stop Redis:

```bash
make stop-redis
```

Open the Redis CLI:

```bash
make redis-cli
```

Redis is used by the application for caching and related runtime infrastructure.

---

# Local Development

Docker is the recommended way to run the complete stack.

For development where the backend or frontend runs directly on the host:

## Backend

```bash
make setup-backend
make run-backend-local
```

The API runs on:

```text
http://localhost:8000
```

## Frontend

```bash
make setup-frontend
make run-frontend-local
```

The Vite development server runs on:

```text
http://localhost:5173
```

---

# Environment Configuration

Backend configuration is managed through Pydantic Settings.

The application loads:

```text
backend/.env
```

## Application

| Variable    | Default      | Description               |
| ----------- | ------------ | ------------------------- |
| `APP_NAME`  | `SafeGround` | Application name          |
| `DEBUG`     | `true`       | Debug mode                |
| `LOG_LEVEL` | `INFO`       | Application logging level |

## PostgreSQL

| Variable      | Default      | Description         |
| ------------- | ------------ | ------------------- |
| `PG_USERNAME` | `postgres`   | PostgreSQL username |
| `PG_PASSWORD` | `postgres`   | PostgreSQL password |
| `PG_HOSTNAME` | `localhost`  | PostgreSQL host     |
| `PG_PORT`     | `5432`       | PostgreSQL port     |
| `PG_DB_NAME`  | `safeground` | Database name       |

## Redis

| Variable    | Default                    | Description          |
| ----------- | -------------------------- | -------------------- |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |

## AWS Bedrock

| Variable          | Default     | Description    |
| ----------------- | ----------- | -------------- |
| `AWS_ACCESS_KEY`  | —           | AWS access key |
| `AWS_SECRET_KEY`  | —           | AWS secret key |
| `AWS_REGION_NAME` | `us-east-1` | AWS region     |

## Mapping

| Variable      | Required | Description              |
| ------------- | -------- | ------------------------ |
| `ORS_API_KEY` | No       | OpenRouteService API key |

## Search and scraping

| Variable            | Required | Description       |
| ------------------- | -------- | ----------------- |
| `SERP_API_KEY`      | No       | SerpAPI key       |
| `FIRECRAWL_API_KEY` | No       | Firecrawl API key |

## Scout

| Variable          | Default | Description                               |
| ----------------- | ------- | ----------------------------------------- |
| `SCOUT_USE_GRAPH` | `false` | Enable the LangGraph Scout execution path |

## Rate limiting

| Variable            | Default | Description                                          |
| ------------------- | ------: | ---------------------------------------------------- |
| `RATE_LIMIT_PER_IP` |    `60` | Maximum requests per IP within the configured window |
| `RATE_LIMIT_WINDOW` |    `60` | Rate-limit window in seconds                         |

Do not commit credentials or secrets to Git.

---

# Testing

Run the backend test suite:

```bash
make test
```

Run tests with coverage:

```bash
make test-cov
```

---

# Code Quality

Format the project:

```bash
make format
```

Run linting:

```bash
make lint
```

---

# Database Seeding

Seed development data with:

```bash
cd backend
python seed_data.py
```

When using the Makefile, use the database/migration targets provided by the root Makefile where applicable.

---

# Privacy by Design

Privacy is a core architectural requirement.

SafeGround is designed around:

* No user account requirement
* No user table
* No intentional IP storage
* Privacy middleware
* Anonymous incident reporting
* One-time receipt tokens
* Hashed receipt tokens rather than storing the raw token
* No application-level browsing history
* Quick-exit functionality

The privacy middleware runs before request handlers so identifying request metadata can be removed before application logic processes the request.

---

# AI and Tooling

Scout uses AWS Bedrock for LLM-powered safety analysis.

The agent can orchestrate tools for:

* Incident lookup
* Route information
* Web search
* Web scraping

The tool system is designed to derive LLM tool configurations from Python tool definitions, allowing tools to be registered without maintaining separate provider-specific schemas manually.

Scout can use either:

```text
Direct LLM + tools
```

or:

```text
LangGraph execution path
```

depending on configuration.

---

# External Integrations

SafeGround can integrate with:

* **AWS Bedrock** — LLM reasoning
* **OpenRouteService** — route information
* **SerpAPI** — web search
* **Firecrawl** — web scraping

Optional integrations are controlled through environment variables.

---

# Development Principles

SafeGround follows several architectural principles:

### Privacy first

Do not collect information that is not required for the application's safety functionality.

### Separation of concerns

API routes should coordinate requests rather than contain business logic.

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

### Agent isolation

Agents interact with application capabilities through tools rather than directly accessing persistence infrastructure.

### Provider abstraction

LLM and external-service integrations are isolated behind infrastructure interfaces where practical.

### Testability

Business logic should remain independently testable without requiring the complete application stack.

---

# Documentation

* [`backend/README.md`](./backend/README.md) — backend architecture, API, agents, tools, database, migrations, and testing.
* [`frontend/README.md`](./frontend/README.md) — frontend architecture, components, state management, maps, API integration, and development.

---