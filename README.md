# Plateforme de Gestion de la Mobilité Internationale

Plateforme web destinée à l'ENSEEIHT (Toulouse-INP) pour centraliser et piloter la mobilité internationale des étudiants (Erasmus+, accords bilatéraux, mobilités entrantes et sortantes). Elle synchronise automatiquement les données depuis **MoveON** (universités partenaires, vœux de mobilité) et **Pégase** (données académiques, référentiels).

---

## Architecture

```
mobility-platform/
├── backend/          # Django + Django Ninja (API REST)
├── frontend/         # Next.js 16 + TypeScript + Tailwind CSS
├── fake-cas/         # Mock CAS (développement/E2E uniquement)
├── fake-moveon-api/  # Mock MoveON (développement uniquement)
├── fake-pegase-api/  # Mock Pégase (développement uniquement)
├── fake-eudonet-api/ # Mock Eudonet (développement uniquement)
├── nginx/            # Reverse proxy (staging/prod)
└── docker-compose.dev.yml   # Dev local — hot-reload, base "mobility_dev"
    docker-compose.test.yml  # Overlay E2E — base "mobility_test" isolée, voir plus bas
    docker-compose.staging.yml
    docker-compose.yml        # Production
```

**Stack technique :**

| Couche | Technologie |
|--------|-------------|
| API backend | Django 5 + Django Ninja |
| Base de données | PostgreSQL 16 (`pgcrypto` pour le chiffrement au repos des données sensibles) |
| Tâches asynchrones | Django-Q2 (`qcluster`) |
| Stockage fichiers | MinIO |
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Authentification | CAS Toulouse-INP (JWT HS256, 15 min) |
| Reverse proxy | Nginx |
| Conteneurisation | Docker + Docker Compose |

> **Images Docker :** chaque environnement (`dev`, `staging`, `prod`) tague son image
> backend/worker/frontend explicitement (`mobility-platform-backend:dev`, `:staging`,
> `:prod`, etc.). Ne retire pas ces tags `image:` des fichiers compose — sans eux,
> Docker réutilise le même nom par défaut pour les trois environnements, et builder
> l'un écrase silencieusement l'image utilisée par un autre.

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

# 3. (Premier démarrage) Appliquer les migrations et charger les référentiels
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
docker compose -f docker-compose.dev.yml run --rm backend python manage.py loaddata \
  app/reference/fixtures/countries.json \
  app/reference/fixtures/departments.json \
  app/reference/fixtures/levels.json \
  app/reference/fixtures/parcours.json \
  app/institutions/fixtures/universities.json \
  app/mobility/fixtures/mobility_categories.json \
  app/mobility/fixtures/agreements.json \
  app/mobility/fixtures/agreement_departments.json
```

Ceci donne une base fonctionnelle mais vide de campagnes/étudiants. Pour un
jeu de données complet (historique, étudiants, vœux...), voir
[Données de démonstration](#données-de-démonstration) plus bas.

Les services disponibles après démarrage :

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API backend | http://localhost:8000/api/v1/ |
| Swagger / OpenAPI | http://localhost:8000/api/v1/docs |
| Admin Django | http://localhost:8000/admin/ |
| MinIO console | http://localhost:9003 |
| Fake CAS | http://localhost:8380 |
| Fake MoveON API | http://localhost:8080 |
| Fake Pégase API | http://localhost:8181 |
| Fake Eudonet API | http://localhost:8282 |
| SonarQube | http://localhost:9001 (`admin` / `admin` à la première connexion) |

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

## Données de démonstration

Une fois les référentiels chargés (étape 3 du démarrage rapide), ce pipeline
reconstruit un jeu de données complet et diversifié : historique réel de 3
campagnes clôturées (vraies transitions FSM + vrai algorithme Gale-Shapley),
une campagne courante, des étudiants entrants, des stages internationaux et
des mobilités complémentaires. Idempotent pour `seed_dev_data` /
`seed_mobility_data` ; `reset_historical_years` **vide et reconstruit** les
données liées aux années (jamais les référentiels).

```bash
# 1. Historique : 5 années clôturées (2020-2021 → 2024-2025), ~35 étudiants
#    par département et par année (~105/an), affectations réelles via Gale-Shapley
docker compose -f docker-compose.dev.yml run --rm backend python manage.py reset_historical_years

# 2. Année courante 2025-2026 (ouverte aux vœux) — pas de commande dédiée,
#    un court script shell suffit
docker compose -f docker-compose.dev.yml run --rm backend python manage.py shell -c "
from app.academic.models import AcademicYear
year = AcademicYear.objects.create(
    label='2025-2026', start_date='2025-09-01', end_date='2026-08-31',
    wishes_open_date='2025-10-01', wishes_close_date='2025-12-15',
)
year.open_recommendation(); year.save(update_fields=['status', 'updated_at'])
year.start_candidature(); year.save(update_fields=['status', 'updated_at'])
"

# 3. 55 étudiants + vœux + 5 accords supplémentaires pour 2025-2026
docker compose -f docker-compose.dev.yml run --rm backend python manage.py seed_dev_data

# 4. Entrants (~60 à 130/an), stages, mobilités complémentaires sur les 6 années
docker compose -f docker-compose.dev.yml run --rm backend python manage.py seed_mobility_data

# 5. 4 comptes de test 2026-2027 (Boursier x FISE/FISA) — utile pour tester le
#    tableau étudiants sur une année distincte de la campagne courante
docker compose -f docker-compose.dev.yml run --rm backend python manage.py seed_test_accounts_2627
```

L'année courante est laissée en statut `candidature` — dérouler la suite du
cycle (clôture des vœux → import → lancement de l'affectation) depuis
l'interface admin permet de tester le workflow complet en direct.

Comptes fake-cas disponibles pour se connecter en tant qu'étudiant (voir
`fake-cas/users.json`, mot de passe `etudiant123` pour tous) :

| Compte | Année | Département | FISE/FISA | Boursier | Profil |
|---|---|---|---|---|---|
| etudiant@etud.n7.fr | 2025-2026 | 3EA | FISA | — | — |
| etudiant2@etud.n7.fr | 2025-2026 | SN | FISE | — | — |
| etudiant3@etud.n7.fr | 2026-2027 | SN | FISE | Oui | Ancien (historique 2025-2026 en 1ING) |
| etudiant4@etud.n7.fr | 2026-2027 | SN | FISA | Oui | Ancien (FISE 2ING en 2025-2026 → FISA 3ING) |
| etudiant5@etud.n7.fr | 2026-2027 | 3EA | FISE | Non | Nouveau (aucun historique) |
| etudiant6@etud.n7.fr | 2026-2027 | 3EA | FISA | Non | Nouveau (aucun historique) |

> **Base de dev vs base de test E2E :** `docker-compose.dev.yml` utilise la
> base `mobility_dev` (persistante, celle que ce pipeline remplit).
> `docker-compose.test.yml` (voir [Tests End-to-End](#4-tests-end-to-end-playwright))
> utilise une base `mobility_test` séparée et sans volume persistant — chaque
> run E2E repart d'une base vierge et ne touche jamais aux données de dev.

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
docker compose -f docker-compose.dev.yml run --rm backend pytest --cov=. --cov-report=html --cov-fail-under=80 -q
```

Le rapport HTML est écrit dans `backend/htmlcov/` (bind-mount, donc accessible côté hôte). Ouvre-le via :

```
backend/htmlcov/index.html
```

**Si tu comptes lancer SonarQube ensuite (section 7)**, une étape supplémentaire
est nécessaire : `backend/coverage.xml` enregistre des chemins relatifs à
`backend/` (ex. `conftest.py`), alors que SonarQube attend des chemins relatifs
à la racine du projet (`backend/conftest.py`). Sans ça, SonarQube ignore
silencieusement la couverture de la quasi-totalité des fichiers backend (vu en
pratique : couverture affichée à ~10% alors que pytest en mesure 84%+) :

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python fix_coverage_paths.py
```

### 3. Frontend

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run lint
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run typecheck
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run test:coverage
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run build
```

### 4. Tests End-to-End (Playwright)

Le plus simple : passer par l'overlay Docker dédié, qui démarre toute la
stack (backend, fake-CAS, frontend) avec les bonnes URLs internes et lance
Playwright dans un conteneur qui a déjà les navigateurs installés :

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up --build --exit-code-from playwright
```

**Interface graphique dans le navigateur** — pour lancer/déboguer les tests un
par un, avec captures d'écran et rejeu pas à pas de chaque action :

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up --build playwright-ui
```

Puis ouvrir **http://localhost:9323**. Si `playwright-report` (voir
ci-dessous) tourne déjà, il occupe le même port : `docker stop
mobility-platform-playwright-report-1` avant de lancer l'UI.

Pour uniquement consulter le rapport HTML d'un run déjà terminé (screenshots,
vidéos, traces), sans relancer les tests :

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up --build playwright-report
```

→ ouvrir http://localhost:9323 également (arrêter l'UI ci-dessus au préalable
si elle tourne, même conflit de port).
    
Ces deux stacks utilisent la même base isolée `mobility_test` que le run
standard — aucun risque pour les données de dev.

Pour lancer Playwright manuellement (hors `docker-compose.test.yml`), deux
variables d'environnement sont nécessaires — sans elles, `e2e/helpers.ts`
retombe sur `http://localhost:3000` / `http://localhost:8000`, qui ne
résolvent pas depuis l'intérieur d'un conteneur :

```bash
docker exec -e E2E_BASE_URL=http://frontend:3000 -e E2E_API_URL=http://backend:8000/api/v1 mobility-platform-frontend-1 npx playwright test
```

### 5. Build des images Docker de production

```bash
docker build -t mobility-backend:local ./backend -f ./backend/Dockerfile
docker build -t mobility-frontend:local ./frontend -f ./frontend/Dockerfile
```

### 6. Scan de sécurité Trivy

```bash
# Linux / macOS
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd)/.trivyignore:/.trivyignore aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed--ignorefile /.trivyignore mobility-backend:local

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd)/.trivyignore:/.trivyignore aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --ignorefile /.trivyignore mobility-frontend:local
```

```powershell
# Windows (PowerShell)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}\.trivyignore:/.trivyignore" aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --ignorefile /.trivyignore mobility-backend:local
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}\.trivyignore:/.trivyignore" aquasec/trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed --ignorefile /.trivyignore mobility-frontend:local
```

> Un exit code 1 sur le scan Trivy signifie que le push échouera aussi en CI.

### 7. Analyse SonarQube (local uniquement — pas en CI)

**Interface web :** http://localhost:9001 (identifiants par défaut `admin` /
`admin` à la première connexion, changement de mot de passe demandé).

Réutilise `backend/coverage.xml` et `frontend/coverage/lcov.info` générés aux
étapes 2 et 3 ci-dessus. Le scanner doit être attaché au réseau Docker et
viser le port interne de SonarQube (`9000`) — `--network host` et
`localhost:9001` ne fonctionnent pas de façon fiable sous Docker Desktop
Windows/Mac.

```bash
docker compose -f docker-compose.dev.yml up -d sonarqube

# Attendre que SonarQube soit prêt (30s à 1-2 min au premier démarrage —
# lancer le scanner trop tôt échoue avec "Failed to query server version")
docker run --rm --network mobility-platform_default curlimages/curl \
  sh -c 'until curl -sf http://sonarqube:9000/api/system/status | grep -q UP; do sleep 3; done'

docker run --rm --network mobility-platform_default \
  -e SONAR_HOST_URL=http://sonarqube:9000 \
  -e SONAR_TOKEN=<TON_TOKEN_SONARQUBE> \
  -v "${PWD}:/usr/src" sonarsource/sonar-scanner-cli
```

Le token se génère dans l'interface SonarQube (http://localhost:9001) via
*Administration → Security → Tokens*.

### 8. Test de charge k6 (local uniquement — pas en CI)

Valide le BNF04 (p95 < 200 ms sous 50 utilisateurs simultanés). Nécessite la
stack up et attachée au réseau Docker — sans `--network`, le nom `backend` ne
se résout pas et toutes les requêtes échouent immédiatement.

```bash
docker compose -f docker-compose.dev.yml up -d

docker run --rm --network mobility-platform_default \
  -e BASE_URL=http://backend:8000/api/v1 \
  -v "${PWD}/performance:/scripts" grafana/k6 run /scripts/load-test-bnf04.js
```

> Le serveur de dev (`manage.py runserver`) n'est pas conçu pour la
> concurrence : les seuils à 50 VUs simultanés ne peuvent être validés
> correctement que contre la stack de production (`docker-compose.yml`,
> gunicorn + workers uvicorn), pas contre `docker-compose.dev.yml`.

---

## CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci.yml`) s'exécute sur chaque push et PR :

1. **Lint** — `ruff check` + `ruff format --check`
2. **Tests backend** — `pytest` avec couverture ≥ 80 % sur PostgreSQL
3. **Lint frontend** — ESLint + vérification TypeScript
4. **Tests frontend** — Vitest
5. **Build Docker** — Build des images backend et frontend
6. **Scan sécurité** — Trivy sur les deux images (CRITICAL + HIGH, bloquant)

L'analyse SonarQube et le test de charge k6 (sections 7 et 8 ci-dessus) sont
des outils de vérification locale, pas encore intégrés au pipeline CI.

Le déploiement staging (`.github/workflows/deploy-staging.yml`) se déclenche automatiquement sur push vers `main`.
