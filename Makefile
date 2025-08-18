# ======================================================================================
# Briefex Makefile — Docker Compose management for dev/prod + Alembic + GHCR
# Default environment is `dev`. Set ENV=prod to enable GHCR publishing targets.
# ======================================================================================

# ----- Configuration ------------------------------------------------------------------
ENV          ?= dev
PROJECT      ?= briefex-$(ENV)
COMPOSE_FILE ?= docker-compose.$(ENV).yml
COMPOSE      ?= docker compose
DC           := $(COMPOSE) -f $(COMPOSE_FILE) -p $(PROJECT)

ALEMBIC      ?= alembic
SERVICE      ?= celery_worker   # default service to exec into for dockerized tasks
DOCKERFILE   ?= Dockerfile

# ----- GHCR Publication Config (effective only with ENV=prod) -------------------------
OWNER        ?= knvovk                # e.g. your GitHub org/user
REPO         ?= briefex               # e.g. repository name
IMAGE        := ghcr.io/$(OWNER)/$(REPO)

# Semver tag for release (override if needed): VER=v1.2.3
VER          ?= v1.0.0
SHORT_SHA    := $(shell git rev-parse --short=7 HEAD)
FULL_SHA     := $(shell git rev-parse HEAD)
LATEST       ?= auto                  # auto|true|false  (auto=разрешить latest только из main)

# Allow publish only in prod
ifeq ($(ENV),prod)
  PUBLISH_GHCR_ALLOWED := yes
else
  PUBLISH_GHCR_ALLOWED := no
endif

# ----- Helpers ------------------------------------------------------------------------
.PHONY: help compose-check prod-guard
help:
	@echo "Make targets (ENV=$(ENV), COMPOSE_FILE=$(COMPOSE_FILE), PROJECT=$(PROJECT))"
	@echo "Docker: build, up, up-build, down, stop, restart, ps, logs, logs-<svc>, pull, destroy, sh-<svc>, exec"
	@echo "Alembic (local): alembic-rev, alembic-up, alembic-up-to, alembic-down, alembic-history"
	@echo "Alembic (dockerized inside $(SERVICE)): alembic-rev, alembic-up, alembic-up-to, alembic-down, alembic-history"
	@echo "GHCR (ENV=prod only): ghcr-login, ghcr-build, ghcr-push, ghcr-publish, ghcr-show"
	@echo "Examples: make ENV=prod ghcr-publish | make logs-celery_worker | make sh-celery_worker"

compose-check:
	@# Verify compose file exists for selected ENV
	@test -f $(COMPOSE_FILE) || (echo "[ERROR] Compose file '$(COMPOSE_FILE)' not found. Set ENV=dev|prod or COMPOSE_FILE=..." && exit 1)

prod-guard:
	@test "$(PUBLISH_GHCR_ALLOWED)" = "yes" || (echo "[ERROR] GHCR publishing is allowed only with ENV=prod" && exit 1)
	@test -n "$(OWNER)" && test "$(OWNER)" != "<owner>" || (echo "[ERROR] Set OWNER=<github_owner>" && exit 1)
	@test -n "$(REPO)"  && test "$(REPO)"  != "<repo>"  || (echo "[ERROR] Set REPO=<repository>" && exit 1)

# ----- Docker Management --------------------------------------------------------------
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

# ----- Alembic Management -------------------------------------------------------------
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

# ----- GHCR Publication (ENV=prod only, single-arch) ----------------------------------
# Требуются переменные окружения:
#   GHCR_USER=<github_username>
#   GHCR_PAT=<personal_access_token_with_write:packages>
.PHONY: ghcr-login ghcr-build ghcr-push ghcr-publish ghcr-show

ghcr-login: prod-guard
	@echo "$$GHCR_PAT" | docker login ghcr.io -u "$$GHCR_USER" --password-stdin

# Single-arch build
ghcr-build: prod-guard
	docker build \
	  -t $(IMAGE):$(VER) \
	  -t $(IMAGE):sha-$(SHORT_SHA) \
	  --label org.opencontainers.image.title=BriefEx \
	  --label org.opencontainers.image.source=https://github.com/$(OWNER)/$(REPO) \
	  --label org.opencontainers.image.version=$(VER) \
	  --label org.opencontainers.image.revision=$(FULL_SHA) \
	  -f $(DOCKERFILE) .

# Push tags (и, при необходимости, latest)
ghcr-push: prod-guard
	docker push $(IMAGE):$(VER)
	docker push $(IMAGE):sha-$(SHORT_SHA)
ifneq ($(LATEST),false)
	@if [ "$(LATEST)" = "true" ] || [ "$$((git rev-parse --abbrev-ref HEAD 2>/dev/null))" = "main" ]; then \
	  docker tag $(IMAGE):$(VER) $(IMAGE):latest; \
	  docker push $(IMAGE):latest; \
	else \
	  echo "[info] 'latest' skipped (LATEST=$(LATEST))"; \
	fi
endif

# Удобная «всё-в-одном» цель (login + build + push)
ghcr-publish: ghcr-login ghcr-build ghcr-push

# Показать манифест и OCI-метки опубликованного образа
ghcr-show: prod-guard
	@echo "==> manifest (single-arch)"
	@docker manifest inspect $(IMAGE):$(VER) || true
	@echo "==> OCI labels (requires 'skopeo' and 'jq')"
	@skopeo inspect docker://$(IMAGE):$(VER) | jq '.Labels' || true
