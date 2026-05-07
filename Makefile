.PHONY: help up down build logs shell test lint migrate

help:
	@echo "Commandes disponibles :"
	@echo "  make up       — Démarrer l'environnement dev"
	@echo "  make down     — Arrêter les containers"
	@echo "  make build    — Rebuilder les images"
	@echo "  make logs     — Afficher les logs"
	@echo "  make shell    — Shell Django"
	@echo "  make test     — Lancer les tests"
	@echo "  make lint     — Lancer ruff"
	@echo "  make migrate  — Appliquer les migrations"
	@echo "  make makemigrations — Créer les migrations"

up:
	docker compose -f docker-compose.dev.yml up

up-d:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

build:
	docker compose -f docker-compose.dev.yml build

logs:
	docker compose -f docker-compose.dev.yml logs -f

shell:
	docker compose -f docker-compose.dev.yml exec backend python manage.py shell

bash:
	docker compose -f docker-compose.dev.yml exec backend bash

test:
	docker compose -f docker-compose.dev.yml exec backend \
		pytest --cov=. --cov-report=term-missing -v

lint:
	docker compose -f docker-compose.dev.yml exec backend ruff check .

format:
	docker compose -f docker-compose.dev.yml exec backend ruff format .

migrate:
	docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

makemigrations:
	docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations

createsuperuser:
	docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

db-backup:
	docker compose -f docker-compose.dev.yml exec db \
		pg_dump -U mobility mobility_dev > backup_$(shell date +%Y%m%d_%H%M%S).sql