# ─────────────────────────────────────────────────────────────────────────────
# SafeGround — Root Makefile
# ─────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ── Configuration ─────────────────────────────────────────────────────────────

COMPOSE := docker compose

API_PORT      ?= 8000
FRONTEND_PORT ?= 5173
POSTGRES_PORT ?= 5432
REDIS_PORT    ?= 6379

BACKEND_CONTAINER  := safeground-backend
FRONTEND_CONTAINER := safeground-frontend
POSTGRES_CONTAINER := safeground-postgres
REDIS_CONTAINER    := safeground-redis

# ── Colors ────────────────────────────────────────────────────────────────────

BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
RED    := \033[31m
RESET  := \033[0m


# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@printf "\n$(BOLD)SafeGround — available targets$(RESET)\n\n"

	@printf "$(BOLD)$(GREEN)Docker / Full Stack$(RESET)\n"
	@printf "  $(BOLD)start$(RESET)              Build and start the full stack\n"
	@printf "  $(BOLD)stop$(RESET)               Stop all containers\n"
	@printf "  $(BOLD)restart$(RESET)            Restart the full stack\n"
	@printf "  $(BOLD)build$(RESET)              Build all Docker images\n"
	@printf "  $(BOLD)rebuild$(RESET)            Rebuild all images without cache\n"
	@printf "  $(BOLD)logs$(RESET)               Follow all container logs\n"
	@printf "  $(BOLD)ps$(RESET)                 Show container status\n"

	@printf "\n$(BOLD)$(GREEN)Backend$(RESET)\n"
	@printf "  $(BOLD)start-backend$(RESET)      Start backend + dependencies\n"
	@printf "  $(BOLD)stop-backend$(RESET)       Stop backend + dependencies\n"
	@printf "  $(BOLD)build-backend$(RESET)      Build backend image\n"
	@printf "  $(BOLD)logs-backend$(RESET)       Follow backend logs\n"
	@printf "  $(BOLD)shell-backend$(RESET)      Open shell inside backend\n"

	@printf "\n$(BOLD)$(GREEN)Frontend$(RESET)\n"
	@printf "  $(BOLD)start-frontend$(RESET)     Start frontend\n"
	@printf "  $(BOLD)stop-frontend$(RESET)      Stop frontend\n"
	@printf "  $(BOLD)build-frontend$(RESET)     Build frontend image\n"
	@printf "  $(BOLD)logs-frontend$(RESET)      Follow frontend logs\n"
	@printf "  $(BOLD)shell-frontend$(RESET)     Open shell inside frontend\n"

	@printf "\n$(BOLD)$(GREEN)Database / Redis$(RESET)\n"
	@printf "  $(BOLD)start-db$(RESET)            Start PostgreSQL\n"
	@printf "  $(BOLD)stop-db$(RESET)             Stop PostgreSQL\n"
	@printf "  $(BOLD)db-shell$(RESET)            Open PostgreSQL shell\n"
	@printf "  $(BOLD)db-migrate$(RESET)          Run Alembic migrations\n"
	@printf "  $(BOLD)db-migration$(RESET)        Create a new migration\n"
	@printf "  $(BOLD)db-downgrade$(RESET)        Roll back one migration\n"
	@printf "  $(BOLD)db-reset$(RESET)            Remove database volume\n"
	@printf "  $(BOLD)start-redis$(RESET)         Start Redis\n"
	@printf "  $(BOLD)stop-redis$(RESET)          Stop Redis\n"
	@printf "  $(BOLD)redis-cli$(RESET)           Open Redis CLI\n"

	@printf "\n$(BOLD)$(GREEN)Local Development$(RESET)\n"
	@printf "  $(BOLD)setup-backend$(RESET)       Create venv and install Python deps\n"
	@printf "  $(BOLD)setup-frontend$(RESET)      Install npm dependencies\n"
	@printf "  $(BOLD)run-backend-local$(RESET)   Run FastAPI locally\n"
	@printf "  $(BOLD)run-frontend-local$(RESET)  Run Vite locally\n"

	@printf "\n$(BOLD)$(GREEN)Testing / Quality$(RESET)\n"
	@printf "  $(BOLD)test$(RESET)               Run backend tests\n"
	@printf "  $(BOLD)test-cov$(RESET)           Run tests with coverage\n"
	@printf "  $(BOLD)format$(RESET)             Format backend code\n"
	@printf "  $(BOLD)lint$(RESET)               Run backend linting\n"

	@printf "\n$(BOLD)$(GREEN)Maintenance$(RESET)\n"
	@printf "  $(BOLD)clean$(RESET)              Remove local build/cache artifacts\n"
	@printf "  $(BOLD)clean-docker$(RESET)       Remove stopped containers/images\n"
	@printf "  $(BOLD)clean-all$(RESET)          Full local cleanup\n"

	@printf "\n"


# ─────────────────────────────────────────────────────────────────────────────
# Full Stack
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: start
start:
	@printf "$(BOLD)Starting SafeGround...$(RESET)\n"
	$(COMPOSE) up --build -d
	@printf "\n$(GREEN)$(BOLD)SafeGround is running.$(RESET)\n"
	@printf "  Frontend: http://localhost:$(FRONTEND_PORT)\n"
	@printf "  API:      http://localhost:$(API_PORT)\n"
	@printf "  API Docs: http://localhost:$(API_PORT)/docs\n"
	@printf "  Postgres: localhost:$(POSTGRES_PORT)\n"
	@printf "  Redis:    localhost:$(REDIS_PORT)\n"

.PHONY: stop
stop:
	@printf "$(BOLD)Stopping SafeGround...$(RESET)\n"
	$(COMPOSE) down

.PHONY: restart
restart:
	$(MAKE) stop
	$(MAKE) start

.PHONY: build
build:
	@printf "$(BOLD)Building all SafeGround images...$(RESET)\n"
	$(COMPOSE) build

.PHONY: rebuild
rebuild:
	@printf "$(BOLD)Rebuilding all images without cache...$(RESET)\n"
	$(COMPOSE) build --no-cache

.PHONY: logs
logs:
	$(COMPOSE) logs -f

.PHONY: ps
ps:
	$(COMPOSE) ps


# ─────────────────────────────────────────────────────────────────────────────
# Backend
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: start-backend
start-backend:
	@printf "$(BOLD)Starting PostgreSQL, Redis and backend...$(RESET)\n"
	$(COMPOSE) up --build -d postgres redis backend
	@printf "$(GREEN)Backend is running on http://localhost:$(API_PORT)$(RESET)\n"

.PHONY: stop-backend
stop-backend:
	$(COMPOSE) stop backend postgres redis

.PHONY: build-backend
build-backend:
	$(COMPOSE) build backend

.PHONY: logs-backend
logs-backend:
	$(COMPOSE) logs -f backend

.PHONY: shell-backend
shell-backend:
	$(COMPOSE) exec backend /bin/bash


# ─────────────────────────────────────────────────────────────────────────────
# Frontend
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: start-frontend
start-frontend:
	@printf "$(BOLD)Starting frontend...$(RESET)\n"
	$(COMPOSE) up --build -d frontend
	@printf "$(GREEN)Frontend is running on http://localhost:$(FRONTEND_PORT)$(RESET)\n"

.PHONY: stop-frontend
stop-frontend:
	$(COMPOSE) stop frontend

.PHONY: build-frontend
build-frontend:
	$(COMPOSE) build frontend

.PHONY: logs-frontend
logs-frontend:
	$(COMPOSE) logs -f frontend

.PHONY: shell-frontend
shell-frontend:
	$(COMPOSE) exec frontend /bin/sh


# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: start-db
start-db:
	@printf "$(BOLD)Starting PostgreSQL...$(RESET)\n"
	$(COMPOSE) up -d postgres

.PHONY: stop-db
stop-db:
	$(COMPOSE) stop postgres

.PHONY: db-shell
db-shell:
	$(COMPOSE) exec postgres \
		psql -U postgres -d safeground

.PHONY: db-migrate
db-migrate:
	@printf "$(BOLD)Running Alembic migrations...$(RESET)\n"
	$(COMPOSE) exec backend alembic upgrade head

.PHONY: db-migration
db-migration:
ifndef MESSAGE
	@printf "$(RED)ERROR: MESSAGE is required.$(RESET)\n"
	@printf "Example: make db-migration MESSAGE=\"add incident status\"\n"
	@exit 1
endif
	$(COMPOSE) exec backend \
		alembic revision --autogenerate -m "$(MESSAGE)"

.PHONY: db-downgrade
db-downgrade:
	$(COMPOSE) exec backend alembic downgrade -1

.PHONY: db-reset
db-reset:
	@printf "$(RED)$(BOLD)WARNING: This will delete the PostgreSQL volume.$(RESET)\n"
	@read -p "Continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(COMPOSE) down -v; \
	else \
		printf "Cancelled.\n"; \
	fi


# ─────────────────────────────────────────────────────────────────────────────
# Redis
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: start-redis
start-redis:
	$(COMPOSE) up -d redis

.PHONY: stop-redis
stop-redis:
	$(COMPOSE) stop redis

.PHONY: redis-cli
redis-cli:
	$(COMPOSE) exec redis redis-cli


# ─────────────────────────────────────────────────────────────────────────────
# Local Development
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: setup-backend
setup-backend:
	@printf "$(BOLD)Setting up Python virtual environment...$(RESET)\n"
	cd backend && python3 -m venv .venv
	cd backend && .venv/bin/pip install --upgrade pip
	cd backend && .venv/bin/pip install -r requirements.txt
	@printf "$(GREEN)Backend setup complete.$(RESET)\n"

.PHONY: setup-frontend
setup-frontend:
	@printf "$(BOLD)Installing frontend dependencies...$(RESET)\n"
	cd frontend && npm install
	@printf "$(GREEN)Frontend setup complete.$(RESET)\n"

.PHONY: run-backend-local
run-backend-local:
	@printf "$(BOLD)Starting FastAPI development server...$(RESET)\n"
	cd backend && uvicorn main:app \
		--host 0.0.0.0 \
		--port $(API_PORT) \
		--reload

.PHONY: run-frontend-local
run-frontend-local:
	@printf "$(BOLD)Starting Vite development server...$(RESET)\n"
	cd frontend && npm run dev -- --host 0.0.0.0 --port $(FRONTEND_PORT)


# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: test
test:
	@printf "$(BOLD)Running backend tests...$(RESET)\n"
	$(COMPOSE) exec backend pytest

.PHONY: test-cov
test-cov:
	@printf "$(BOLD)Running tests with coverage...$(RESET)\n"
	$(COMPOSE) exec backend \
		pytest --cov=. --cov-report=term-missing

.PHONY: format
format:
	@printf "$(BOLD)Formatting backend code...$(RESET)\n"
	$(COMPOSE) exec backend \
		sh -c "ruff format . 2>/dev/null || true"

.PHONY: lint
lint:
	@printf "$(BOLD)Linting backend code...$(RESET)\n"
	$(COMPOSE) exec backend \
		sh -c "ruff check . 2>/dev/null || true"


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	@printf "$(BOLD)Cleaning local artifacts...$(RESET)\n"
	rm -rf backend/.pytest_cache
	rm -rf backend/.coverage
	rm -rf backend/htmlcov
	rm -rf backend/**/__pycache__
	rm -rf frontend/dist
	rm -rf frontend/.vite
	@printf "$(GREEN)Clean complete.$(RESET)\n"

.PHONY: clean-docker
clean-docker:
	@printf "$(BOLD)Removing stopped containers...$(RESET)\n"
	docker container prune -f
	@printf "$(BOLD)Removing dangling images...$(RESET)\n"
	docker image prune -f

.PHONY: clean-all
clean-all:
	$(MAKE) clean
	$(MAKE) clean-docker
	rm -rf backend/.venv
	rm -rf frontend/node_modules
	@printf "$(GREEN)$(BOLD)Full cleanup complete.$(RESET)\n"