# ==============================================================================
# Briefex Makefile — Docker Compose management for dev/prod + Alembic helpers
# Default environment is `dev`. Override with ENV=prod (or custom) as needed.
# Examples:
#   make up                          # dev up
#   make ENV=prod up                 # prod up (uses docker-compose.prod.yml)
#   make logs                        # follow all logs
#   make logs-celery_worker          # follow a single service
#   make sh-celery_worker            # shell into service (bash/sh)
#   make exec service=celery_worker cmd="alembic upgrade head"  # run in container
#   make alembic-up                 # Alembic inside container (dev convenience)
# ==============================================================================

# ----- Configuration -----------------------------------------------------------
ENV          ?= dev
PROJECT      ?= briefex-$(ENV)
COMPOSE_FILE ?= docker-compose.$(ENV).yml
COMPOSE      ?= docker compose
DC           := $(COMPOSE) -f $(COMPOSE_FILE) -p $(PROJECT)

ALEMBIC      ?= alembic
SERVICE      ?= celery_worker   # default service to exec into for dockerized tasks

# ----- Helpers ----------------------------------------------------------------
.PHONY: help compose-check
help:
	@echo "Make targets (ENV=$(ENV), COMPOSE_FILE=$(COMPOSE_FILE), PROJECT=$(PROJECT))"
	@echo "Docker: build, up, up-build, down, stop, restart, ps, logs, logs-<svc>, pull, destroy, sh-<svc>, exec"
	@echo "Alembic (local): alembic-rev, alembic-up, alembic-up-to, alembic-down, alembic-history"
	@echo "Alembic (dockerized inside $(SERVICE)): alembic-rev, alembic-up, alembic-up-to, alembic-down, alembic-history"
	@echo "Examples: make up | make ENV=prod up | make logs-celery_worker | make sh-celery_worker"

compose-check:
	@# Verify compose file exists for selected ENV
	@test -f $(COMPOSE_FILE) || (echo "[ERROR] Compose file '$(COMPOSE_FILE)' not found. Set ENV=dev|prod or COMPOSE_FILE=..." && exit 1)

# ----- Docker Management -------------------------------------------------------
.PHONY: build up up-build down stop restart ps logs pull destroy

build: compose-check
	$(DC) build --pull

up: compose-check
	$(DC) up -d

up-build: compose-check
	$(DC) up -d --build

down: compose-check
	$(DC) down

stop: compose-check
	$(DC) stop

restart: compose-check
	$(DC) restart

ps: compose-check
	$(DC) ps

logs: compose-check
	$(DC) logs -f --tail=200

pull: compose-check
	$(DC) pull

# DANGER: also removes named volumes of this project
destroy: compose-check
	$(DC) down -v

# Per-service helpers
.PHONY: exec
exec: compose-check
	@test -n "$(service)" || (echo "Usage: make exec service=<name> cmd=\"...\"" && exit 1)
	@test -n "$(cmd)" || (echo "Usage: make exec service=<name> cmd=\"...\"" && exit 1)
	$(DC) exec $(service) sh -lc '$(cmd)'

# Pattern rules for convenience: logs-<service>, sh-<service>
.PHONY: logs-% sh-%
logs-%: compose-check
	$(DC) logs -f $*

sh-%: compose-check
	@$(DC) exec $* sh -lc 'command -v bash >/dev/null 2>&1 && exec bash || exec sh'

# ----- Alembic Management -----------------------------------------------------
.PHONY: alembic-rev alembic-up alembic-up-to alembic-down alembic-history

alembic-rev: compose-check
	$(DC) exec $(SERVICE) alembic revision --autogenerate -m "${message}"

alembic-up: compose-check
	$(DC) exec $(SERVICE) alembic upgrade head

alembic-up-to: compose-check
	@test -n "${to}" || (echo "Usage: make alembic-up-to to=<revision>" && exit 1)
	$(DC) exec $(SERVICE) alembic upgrade ${to}

alembic-down: compose-check
	@test -n "${to}" || (echo "Usage: make alembic-down to=<revision>" && exit 1)
	$(DC) exec $(SERVICE) alembic downgrade ${to}

alembic-history: compose-check
	$(DC) exec $(SERVICE) alembic history --verbose
