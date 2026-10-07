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

.PHONY: help setup setup-local start awake stop logs dev dev-local down indicators reports notes citizens migrate data demo test test-backend \
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
	$(MAKE) data
	@echo "✓ Installation terminée. Lancez maintenant : make start"

setup-local: .env ## Installation sans Docker (uv et npm) pour les tests et l'éditeur
	cd backend && uv sync
	cd frontend && npm ci

start: .env ## ★ Lance MAJAL en arrière-plan et ouvre le navigateur
	docker compose up -d --build -V
	@printf "Démarrage de MAJAL"; \
	for i in $$(seq 1 90); do \
		curl -sf -o /dev/null http://localhost:3000 && break; printf "."; sleep 2; \
	done; echo
	@curl -sf -o /dev/null http://localhost:3000 \
		&& { echo "✓ MAJAL est prêt : http://localhost:3000"; open http://localhost:3000 2>/dev/null || true; } \
		|| { echo "MAJAL ne répond pas encore. Voir les messages : make logs"; exit 1; }
	@$(MAKE) --no-print-directory awake

# Empêche la mise en veille du Mac (et de l'écran) tant que MAJAL tourne : caffeinate
# (commande de macOS) est lancé en arrière-plan, au plus 12 heures, et arrêté par make stop.
CAFFEINATE_PID := .majal-caffeinate.pid
awake:
	@if command -v caffeinate >/dev/null 2>&1; then \
		if [ -f $(CAFFEINATE_PID) ] && kill -0 $$(cat $(CAFFEINATE_PID)) 2>/dev/null; then \
			echo "✓ Mise en veille déjà empêchée"; \
		else \
			nohup caffeinate -dims -t 43200 >/dev/null 2>&1 & echo $$! > $(CAFFEINATE_PID); \
			echo "✓ Mise en veille du Mac empêchée tant que MAJAL tourne (12 h au plus ; make stop la rétablit)"; \
		fi; \
	fi

stop: ## ★ Arrête MAJAL (et rétablit la mise en veille du Mac)
	docker compose down
	@if [ -f $(CAFFEINATE_PID) ]; then \
		kill $$(cat $(CAFFEINATE_PID)) 2>/dev/null || true; rm -f $(CAFFEINATE_PID); \
		echo "✓ Mise en veille du Mac rétablie"; \
	fi

logs: ## Affiche les messages de MAJAL (Ctrl+C pour quitter l'affichage)
	docker compose logs -f --tail 50

dev: .env ## Lance MAJAL au premier plan, avec les messages (Ctrl+C pour arrêter)
	@# --build: rebuilds images when dependencies changed (instant otherwise);
	@# -V: refreshes node_modules so it always matches the image.
	docker compose up --build -V

dev-local: ## Lance backend et frontend sans Docker (sans base de données)
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

down: ## Arrête tous les services Docker
	docker compose down

migrate: ## Applique les migrations de la base
	docker compose run --rm backend alembic upgrade head

data: .env ## (Re)construit les données : limites, équipements, routes, fond de carte
	docker compose up -d db redis
	docker compose run --rm -T backend alembic upgrade head
	docker compose run --rm -T backend python -m app.ingestion run $(if $(REFRESH),--refresh,)
	./scripts/fetch_basemap.sh
	docker compose run --rm -T backend python -m app.services.indicators compute

indicators: ## Recalcule les indicateurs (après une modification de la grille)
	docker compose run --rm -T backend python -m app.services.indicators compute

reports: ## Pré-génère les rapports de toutes les unités (cache pour les démonstrations)
	docker compose run --rm -T backend python -m app.services.reports pregenerate $(or $(TERRITORY),rabat) $(if $(FORCE),--force,)

notes: ## Écrit les notes de demande de données (Word et PDF) dans docs/notes-demande/<territoire>/
	docker compose run --rm -T backend python -m app.services.data_needs notes $(or $(TERRITORY),rabat)

citizens: ## Importe et analyse les contributions fictives (IA locale), puis évalue
	docker compose run --rm -T backend python -m app.services.citizens import-fictif $(or $(TERRITORY),rabat)
	docker compose run --rm -T backend python -u -m app.services.citizens analyze $(or $(TERRITORY),rabat) $(if $(FORCE),--force,)
	docker compose run --rm -T backend python -m app.services.citizens evaluate $(or $(TERRITORY),rabat)

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
