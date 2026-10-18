# Taskboard developer commands. Requires Docker (with Compose), uv, Node.js 24 and Terraform.
SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

COMPOSE      ?= docker compose
TEST_COMPOSE ?= docker compose -f $(CURDIR)/docker-compose.test.yml
TEST_PG_PORT ?= 55432
TEST_REDIS_PORT ?= 56379
TEST_DATABASE_URL ?= postgresql+psycopg://taskboard_test:taskboard_test@127.0.0.1:$(TEST_PG_PORT)/taskboard_test
TEST_REDIS_URL ?= redis://127.0.0.1:$(TEST_REDIS_PORT)/0

.PHONY: help env up down admin fmt lint typecheck test test-api test-ui tf-check smoke

help: ## List the available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

env: ## Create .env with generated secrets if it does not exist
	@scripts/gen-env.sh

up: env ## Build and start the stack (UI on http://localhost:3000)
	$(COMPOSE) up --build -d --wait

down: ## Stop the stack (data volumes are kept)
	$(COMPOSE) down

admin: env ## Create the first admin from ADMIN_EMAIL/ADMIN_PASSWORD in .env
	set -a; source .env; set +a; \
	$(COMPOSE) run --rm --no-deps -e ADMIN_EMAIL -e ADMIN_PASSWORD api taskboard-admin create-admin

fmt: ## Format all code
	cd api && uv run ruff format src tests migrations && uv run ruff check --fix src tests migrations
	cd ui && npm run format
	terraform -chdir=infra fmt -recursive

lint: ## Lint and check formatting
	cd api && uv run ruff check src tests migrations && uv run ruff format --check src tests migrations
	cd ui && npm run lint && npm run format:check

typecheck: ## Static type checks
	cd api && uv run mypy
	cd ui && npm run typecheck

test: test-api test-ui ## Run both test suites with coverage thresholds

test-api: ## API unit and integration tests (starts throwaway PostgreSQL and Redis)
	TEST_PG_PORT=$(TEST_PG_PORT) TEST_REDIS_PORT=$(TEST_REDIS_PORT) $(TEST_COMPOSE) up -d --wait
	trap '$(TEST_COMPOSE) down -v' EXIT; \
	cd api && TEST_DATABASE_URL='$(TEST_DATABASE_URL)' TEST_REDIS_URL='$(TEST_REDIS_URL)' \
	  uv run pytest --cov --cov-report=term

test-ui: ## UI tests with coverage
	cd ui && npm test

tf-check: ## Terraform format and validation (no cloud access needed)
	terraform -chdir=infra fmt -check -recursive
	terraform -chdir=infra/envs/dev init -backend=false -input=false
	terraform -chdir=infra/envs/dev validate

smoke: ## End-to-end smoke test through the UI of a running stack
	scripts/smoke.sh
