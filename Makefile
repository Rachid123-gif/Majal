# MAJAL — commandes du projet. Tapez `make help` pour la liste.
# Avec Docker installé, tout tourne dans Docker. Sans Docker, les commandes de test et de
# vérification utilisent uv (Python) et npm directement sur la machine.

SHELL := /bin/bash
DOCKER := $(shell command -v docker 2>/dev/null)

ifdef DOCKER
BACKEND  := docker compose run --rm --no-deps backend
FRONTEND := docker compose run --rm --no-deps frontend
else
BACKEND  := cd backend && uv run
FRONTEND := cd frontend &&
endif

.PHONY: help setup setup-local dev dev-local down migrate data demo test test-backend \
        test-frontend lint check-config backup restore

help: ## Affiche cette aide
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

.env:
	cp .env.example .env
	@echo "→ Fichier .env créé à partir de .env.example"

setup: .env ## Première installation (Docker) : construit les images et prépare la base
	docker compose build
	docker compose up -d db redis
	docker compose run --rm backend alembic upgrade head
	@echo "✓ Installation terminée. Lancez maintenant : make dev"

setup-local: .env ## Installation sans Docker (uv et npm) pour les tests et l'éditeur
	cd backend && uv sync
	cd frontend && npm ci

dev: .env ## Lance MAJAL (Docker) : http://localhost:3000
	docker compose up

dev-local: ## Lance backend et frontend sans Docker (sans base de données)
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

down: ## Arrête tous les services Docker
	docker compose down

migrate: ## Applique les migrations de la base
	docker compose run --rm backend alembic upgrade head

data: ## (Re)construit toutes les données — disponible à l'étape 1
	@echo "Pas encore disponible : les imports arrivent à l'étape 1."

demo: ## Lance le mode démonstration hors ligne — disponible à l'étape 7
	@echo "Pas encore disponible : le mode démonstration arrive à l'étape 7."

test: test-backend test-frontend ## Lance tous les tests

test-backend:
	$(BACKEND) pytest -q

test-frontend:
	$(FRONTEND) npm test

lint: ## Vérifie le style et le typage (Python et TypeScript)
	$(BACKEND) ruff check .
	$(BACKEND) ruff format --check .
	$(BACKEND) mypy app tests
	$(FRONTEND) npm run lint
	$(FRONTEND) npm run format:check
	$(FRONTEND) npm run typecheck

check-config: ## Vérifie les fichiers YAML de config/ et explique les erreurs en français
	$(BACKEND) python -m app.config_loader

backup: ## Sauvegarde la base dans backups/
	@mkdir -p backups
	docker compose exec -T db pg_dump -U $${POSTGRES_USER:-majal} -Fc $${POSTGRES_DB:-majal} \
		> backups/majal-$$(date +%Y%m%d-%H%M%S).dump
	@ls -1t backups | head -1 | sed 's/^/✓ Sauvegarde créée : backups\//'

restore: ## Restaure une sauvegarde : make restore FILE=backups/xxx.dump (remplace la base actuelle)
	@test -n "$(FILE)" || (echo "Indiquez le fichier : make restore FILE=backups/xxx.dump" && exit 1)
	@read -p "La base actuelle sera remplacée par $(FILE). Continuer ? [o/N] " ok && [ "$$ok" = "o" ]
	docker compose exec -T db pg_restore -U $${POSTGRES_USER:-majal} -d $${POSTGRES_DB:-majal} \
		--clean --if-exists < $(FILE)
	@echo "✓ Base restaurée depuis $(FILE)"
