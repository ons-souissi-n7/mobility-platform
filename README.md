# Plateforme de Gestion de la Mobilité Internationale

Plateforme web destinée à l'ENSEEIHT (Toulouse-INP) pour centraliser et piloter la mobilité internationale des étudiants (Erasmus+, accords bilatéraux, mobilités entrantes et sortantes). Elle synchronise automatiquement les données depuis **MoveON** (universités partenaires, vœux de mobilité) et **Pégase** (données académiques, référentiels).

---

## Table des matières

- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Démarrage rapide (développement)](#démarrage-rapide-développement)
- [Variables d'environnement](#variables-denvironnement)
- [Commandes Docker](#commandes-docker)
- [Qualité du code](#qualité-du-code)
- [Tests](#tests)
- [Migrations](#migrations)
- [Données initiales](#données-initiales)
- [CI/CD](#cicd)
- [Vérification locale avant push](#vérification-locale-avant-push)
- [Déploiement staging / production](#déploiement-staging--production)

---

## Architecture

```
mobility-platform/
├── backend/          # Django + Django Ninja (API REST)
├── frontend/         # Next.js 15 + TypeScript + Tailwind CSS
├── fake-moveon-api/  # Mock MoveON (développement uniquement)
├── fake-pegase-api/  # Mock Pégase (développement uniquement)
├── nginx/            # Reverse proxy (staging/prod)
└── docker-compose.dev.yml    # Environnement de développement
    docker-compose.staging.yml
    docker-compose.yml        # Production
```

**Stack technique :**

| Couche | Technologie |
|--------|-------------|
| API backend | Django 4 + Django Ninja |
| Base de données | PostgreSQL 16 |
| Tâches asynchrones | Django-Q2 (`qcluster`) |
| Stockage fichiers | MinIO |
| Frontend | Next.js 15 + TypeScript + Tailwind CSS |
| Authentification | CAS Toulouse-INP + OIDC |
| Reverse proxy | Nginx |
| Conteneurisation | Docker + Docker Compose |

**Domaines fonctionnels (apps Django) :**

- `academic` — gestion des années académiques
- `audit` — journalisation des actions
- `imports` — suivi des rapports d'import
- `institutions` — universités partenaires (sync MoveON)
- `mobility` — accords, cadres d'accords, quotas (sync MoveON)
- `reference` — référentiels : pays, départements, niveaux, parcours (sync Pégase)
- `students` — gestion des étudiants et inscriptions annuelles (sync Pégase + MoveON)
- `incoming` / `outgoing` — mobilités entrantes et sortantes
- `internships` — stages à l'international
- `integrations` — clients API MoveON et Pégase

---

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.20 (intégré dans Docker Desktop)
- `make` (optionnel, pour les raccourcis)

---

## Démarrage rapide (développement)

```bash
# 1. Copier et adapter les variables d'environnement
cp .env.example .env

# 2. Construire et démarrer tous les services
docker compose -f docker-compose.dev.yml up --build

# 3. (Premier démarrage) Charger les données initiales
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata \
  app/reference/fixtures/countries.json \
  app/reference/fixtures/departments.json \
  app/reference/fixtures/levels.json \
  app/reference/fixtures/parcours.json \
  app/institutions/fixtures/universities.json
```

Les services disponibles après démarrage :

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API backend | http://localhost:8000/api/v1/ |
| Swagger / OpenAPI | http://localhost:8000/api/v1/docs |
| Admin Django | http://localhost:8000/admin/ |
| MinIO console | http://localhost:9003 |
| Fake MoveON API | http://localhost:8080 |
| Fake Pégase API | http://localhost:8181 |

> **Note :** Le worker (`qcluster`) NE recharge PAS automatiquement le code. Après modification du backend, relancer : `docker compose -f docker-compose.dev.yml restart worker`

---

## Variables d'environnement

Copier `.env.example` en `.env` et renseigner les valeurs :

```bash
cp .env.example .env
```

| Variable | Description | Obligatoire en prod |
|----------|-------------|---------------------|
| `SECRET_KEY` | Clé secrète Django (générer avec `django.core.management.utils.get_random_secret_key()`) | Oui |
| `POSTGRES_DB` | Nom de la base de données | Oui |
| `POSTGRES_USER` | Utilisateur PostgreSQL | Oui |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | Oui |
| `ALLOWED_HOSTS` | Hosts autorisés (séparés par virgule) | Oui |
| `SENTRY_DSN` | DSN Sentry pour le monitoring d'erreurs | Non |
| `MINIO_ROOT_USER` | Accès MinIO | Oui |
| `MINIO_ROOT_PASSWORD` | Mot de passe MinIO | Oui |
| `MOVEON_API_URL` | URL de l'API MoveON | Oui |
| `MOVEON_API_KEY` | Clé d'API MoveON | Oui |
| `PEGASE_API_URL` | URL de l'API Pégase | Oui |
| `CAS_SERVER_URL` | URL du serveur CAS (ex: `https://cas.toulouse-inp.fr/cas/`) | Non |

---

## Commandes Docker

### Via Makefile (raccourcis)

```bash
make up           # Démarrer en développement (foreground)
make up-d         # Démarrer en développement (background)
make down         # Arrêter et supprimer les containers
make build        # Rebuilder les images
make logs         # Suivre les logs en temps réel
make shell        # Ouvrir le shell Django
make bash         # Ouvrir un bash dans le container backend
make test         # Lancer les tests avec couverture
make lint         # Lancer ruff (vérification)
make format       # Formater le code avec ruff
make migrate      # Appliquer les migrations
make makemigrations  # Créer les fichiers de migration
make createsuperuser # Créer un superutilisateur Django
make db-backup    # Sauvegarder la base de données
```

### Commandes complètes

#### Démarrage / Arrêt

```bash
# Démarrer tous les services
docker compose -f docker-compose.dev.yml up

# Démarrer en arrière-plan
docker compose -f docker-compose.dev.yml up -d

# Arrêter les containers (conserver les volumes)
docker compose -f docker-compose.dev.yml down

# Arrêter et supprimer les volumes (reset complet)
docker compose -f docker-compose.dev.yml down -v

# Rebuilder une image spécifique
docker compose -f docker-compose.dev.yml build backend

# Restart d'un seul service (ex: worker après modification du code)
docker compose -f docker-compose.dev.yml restart worker
```

#### Logs

```bash
# Tous les services
docker compose -f docker-compose.dev.yml logs -f

# Un seul service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f worker
```

#### Shell / Debug

```bash
# Shell Django interactif
docker compose -f docker-compose.dev.yml exec backend python manage.py shell

# Bash dans le container backend
docker compose -f docker-compose.dev.yml exec backend bash

# Vérification système Django
docker compose -f docker-compose.dev.yml exec backend python manage.py check
```

---

## Qualité du code

### Backend (Python / ruff)

```bash
# Vérifier le style et les erreurs
docker compose -f docker-compose.dev.yml exec backend ruff check .

# Formatter automatiquement
docker compose -f docker-compose.dev.yml exec backend ruff format .

# Vérifier le formatage sans modifier
docker compose -f docker-compose.dev.yml exec backend ruff format --check .
```

### Frontend (ESLint + TypeScript)

```bash
# Linter ESLint
docker compose -f docker-compose.dev.yml exec frontend npm run lint

# Vérification TypeScript (sans compilation)
docker compose -f docker-compose.dev.yml exec frontend npm run typecheck
```

---

## Tests

### Backend

```bash
# Lancer tous les tests avec couverture
docker compose -f docker-compose.dev.yml exec backend pytest --cov=. --cov-report=term-missing -v

# Tests d'un module spécifique
docker compose -f docker-compose.dev.yml exec backend pytest app/institutions/tests/ -v

# Tests avec rapport XML (pour CI)
docker compose -f docker-compose.dev.yml exec backend pytest --cov=. --cov-report=xml --cov-fail-under=80
```

### Frontend

```bash
# Lancer les tests Vitest
docker compose -f docker-compose.dev.yml exec frontend npm test

# Mode watch
docker compose -f docker-compose.dev.yml exec frontend npm run test:watch
```

---

## Migrations

```bash
# Créer les migrations après modification des modèles
docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations

# Appliquer les migrations
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Afficher les migrations en attente
docker compose -f docker-compose.dev.yml exec backend python manage.py showmigrations
```

---

## Données initiales

```bash
# Charger les référentiels (pays, départements, niveaux, parcours)
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata \
  app/reference/fixtures/countries.json \
  app/reference/fixtures/departments.json \
  app/reference/fixtures/levels.json \
  app/reference/fixtures/parcours.json

# Charger les universités partenaires
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata \
  app/institutions/fixtures/universities.json

# Créer un compte administrateur
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

# Sauvegarder la base de données
docker compose -f docker-compose.dev.yml exec db \
  pg_dump -U mobility mobility_dev > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci.yml`) s'exécute sur chaque push et PR :

1. **Lint** — `ruff check` + `ruff format --check`
2. **Tests backend** — `pytest` avec couverture ≥ 80 % sur PostgreSQL
3. **Lint frontend** — ESLint + vérification TypeScript
4. **Tests frontend** — Vitest
5. **Build Docker** — Build des images backend et frontend
6. **Scan sécurité** — Trivy sur les deux images (CRITICAL + HIGH, bloquant)

Le déploiement staging (`.github/workflows/deploy-staging.yml`) se déclenche automatiquement sur push vers `main`.

---

## Vérification locale avant push

Reproduire l'intégralité du pipeline CI/CD en local avant de pousser une branche.

### 1. Backend — qualité du code

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff check .
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff format --check .
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py check
```

### 2. Backend — migrations

```bash
# Vérifier qu'aucune migration n'a été oubliée
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py makemigrations --check --dry-run

# Appliquer les migrations (requis avant les tests)
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
```

### 3. Backend — tests avec couverture

```bash
# Couverture minimale requise : 80 %
docker compose -f docker-compose.dev.yml run --rm backend pytest --cov=. --cov-report=xml --cov-fail-under=80 -v
```

### 4. Frontend — qualité du code et tests

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run lint
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run typecheck
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm test
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run build
```

### 5. Build des images Docker de production

```bash
docker build -t mobility-backend:local ./backend -f ./backend/Dockerfile
docker build -t mobility-frontend:local ./frontend -f ./frontend/Dockerfile
```

### 6. Scan de sécurité Trivy

Reproduit exactement le job **Scan sécurité** du CI (CRITICAL + HIGH, bloquant).

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed \
  mobility-backend:local

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed \
  mobility-frontend:local
```

> Un exit code 1 sur le scan Trivy signifie que le push échouera aussi en CI.

---

## Déploiement staging / production

### Variables d'environnement requises

Créer un fichier `.env` sur le serveur (ne jamais commiter ce fichier) :

```bash
SECRET_KEY=<générer avec python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
POSTGRES_DB=mobility
POSTGRES_USER=mobility
POSTGRES_PASSWORD=<mot_de_passe_fort>
ALLOWED_HOSTS=mobility.enseeiht.fr,www.mobility.enseeiht.fr
SENTRY_DSN=<dsn_sentry>
MINIO_ROOT_USER=<utilisateur_minio>
MINIO_ROOT_PASSWORD=<mot_de_passe_minio>
MOVEON_API_URL=https://api.moveon.com/v1
MOVEON_API_KEY=<clé_moveon>
PEGASE_API_URL=<url_pegase>
```

### Démarrage (production)

```bash
# Premier déploiement
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py loaddata \
  app/reference/fixtures/countries.json \
  app/reference/fixtures/departments.json \
  app/reference/fixtures/levels.json \
  app/reference/fixtures/parcours.json

# Mise à jour
git pull origin main
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
```

### Secrets GitHub Actions (pour déploiement automatique)

Configurer dans **Settings → Secrets and variables → Actions** :

| Secret | Description |
|--------|-------------|
| `STAGING_SSH_KEY` | Clé SSH privée pour accéder au serveur |
| `STAGING_HOST` | Adresse IP ou hostname du serveur staging |
| `STAGING_USER` | Utilisateur SSH |
| `STAGING_PATH` | Chemin du projet sur le serveur |
