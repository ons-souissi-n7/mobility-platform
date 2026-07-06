# Plateforme de Gestion de la Mobilité Internationale

Plateforme web destinée à l'ENSEEIHT (Toulouse-INP) pour centraliser et piloter la mobilité internationale des étudiants (Erasmus+, accords bilatéraux, mobilités entrantes et sortantes). Elle synchronise automatiquement les données depuis **MoveON** (universités partenaires, vœux de mobilité) et **Pégase** (données académiques, référentiels).

---

## Architecture

```
mobility-platform/
├── backend/          # Django + Django Ninja (API REST)
├── frontend/         # Next.js 15 + TypeScript + Tailwind CSS
├── fake-moveon-api/  # Mock MoveON (développement uniquement)
├── fake-pegase-api/  # Mock Pégase (développement uniquement)
├── nginx/            # Reverse proxy (staging/prod)
└── docker-compose.dev.yml
    docker-compose.staging.yml
    docker-compose.yml        # Production
```

**Stack technique :**

| Couche | Technologie |
|--------|-------------|
| API backend | Django 5 + Django Ninja |
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

---

## Démarrage rapide (développement)

```bash
# 1. Copier et adapter les variables d'environnement
cp .env.example .env

# 2. Construire et démarrer tous les services
docker compose -f docker-compose.dev.yml up --build

# 3. (Premier démarrage) Appliquer les migrations et charger les données initiales
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
docker compose -f docker-compose.dev.yml run --rm backend python manage.py loaddata \
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

## Commandes essentielles

```bash
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

# Logs
docker compose -f docker-compose.dev.yml logs -f backend
```

---

## Migrations

```bash
# Créer les migrations après modification des modèles
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py makemigrations

# Appliquer les migrations
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate

# Vérifier qu'aucune migration n'a été oubliée
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py makemigrations --check --dry-run
```

---

## Vérification locale avant push

Reproduire l'intégralité du pipeline CI/CD en local avant de pousser une branche.

### 1. Backend — formatage et lint

```bash
# Appliquer le formatage automatique
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff format .

# Vérifier lint et formatage
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff check .
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff format --check .

# Checks Django (modèles, config)
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py check
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py makemigrations --check --dry-run
```

### 2. Backend — tests avec couverture

```bash
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
docker compose -f docker-compose.dev.yml run --rm backend pytest --cov=. --cov-report=xml --cov-fail-under=80 -v
```

### 3. Frontend

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run lint
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run typecheck
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm test
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run build
```

### 4. Build des images Docker de production

```bash
docker build -t mobility-backend:local ./backend -f ./backend/Dockerfile
docker build -t mobility-frontend:local ./frontend -f ./frontend/Dockerfile
```

### 5. Scan de sécurité Trivy

```bash
# Linux / macOS
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/.trivyignore:/.trivyignore \
  aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed \
  --ignorefile /.trivyignore mobility-backend:local

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/.trivyignore:/.trivyignore \
  aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed \
  --ignorefile /.trivyignore mobility-frontend:local
```

```powershell
# Windows (PowerShell)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}\.trivyignore:/.trivyignore" aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --ignorefile /.trivyignore mobility-backend:local
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}\.trivyignore:/.trivyignore" aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --ignorefile /.trivyignore mobility-frontend:local
```

> Un exit code 1 sur le scan Trivy signifie que le push échouera aussi en CI.

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
