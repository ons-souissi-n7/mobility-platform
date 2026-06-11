# Gestion_mobilité
## Setup & Development
### Docker Commands
#### Start the development environment:
```bash
docker compose -f docker-compose.dev.yml up --build
```
#### Stop the development environment:
```bash
docker compose -f docker-compose.dev.yml down
```
#### Restart all services:

```bash
docker compose -f docker-compose.dev.yml restart
```
### Load Fixtures and Data
Load initial data into the database:
```bash
# Load reference data (countries, departments, levels, parcours)
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/countries.json
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/departments.json
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/levels.json
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/parcours.json
# Load institutions fixtures
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/institutions/fixtures/universities.json
```
### Code Quality

#### Backend
Format Python code with ruff:
```bash
docker compose -f docker-compose.dev.yml run --rm backend ruff format .
```
Check code formatting without making changes:
```bash
docker compose -f docker-compose.dev.yml run --rm backend ruff format --check .
```
Run checks manually:
```bash
# Django system check
docker compose -f docker-compose.dev.yml run --rm --no-deps backend python manage.py check
# Lint with ruff
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff check .
# Check formatting with ruff
docker compose -f docker-compose.dev.yml run --rm --no-deps backend ruff format --check .
# Run tests
docker compose -f docker-compose.dev.yml run --rm backend pytest
```

#### Frontend
Run ESLint:
```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run lint
```
Check TypeScript types without compilation:
```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps frontend npm run typecheck
```
Run tests
```bash
docker compose -f docker-compose.dev.yml build frontend
```

### Database Migrations
Create migration files after model changes:
```bash
docker compose -f docker-compose.dev.yml run --rm backend python manage.py makemigrations
```
Apply migrations to the database:
```bash
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
```