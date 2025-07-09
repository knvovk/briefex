export POSTGRES_USER
export POSTGRES_PASSWORD
export POSTGRES_DB
export POSTGRES_PORT

DC		= docker compose
ALEMBIC	= alembic

# --- Docker Management ----------------------------------------------------------------
.PHONY: build up down restart ps logs

build:
	$(DC) up -d --build

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart db

ps:
	$(DC) ps

logs:
	$(DC) logs -f db

# --- Alembic Management ---------------------------------------------------------------
.PHONY: alembic-rev alembic-up alembic-up-to alembic-down alembic-history

alembic-rev:
	$(ALEMBIC) revision --autogenerate -m "${message}"

alembic-up:
	$(ALEMBIC) upgrade head

alembic-up-to:
	$(ALEMBIC) upgrade ${to}

alembic-down:
	$(ALEMBIC) downgrade ${to}

alembic-history:
	$(ALEMBIC) history --verbose
