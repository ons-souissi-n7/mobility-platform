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
# Load reference data (countries, departments)
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/countries.json
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/reference/fixtures/departments.json
# Load institutions fixtures
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata app/institutions/fixtures/universities.json
```
### Code Quality
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
### Git Commit Convention
Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
```
<type>(<scope>): <description>

Closes: #<issue>   # ferme l'issue
Refs: #<issue>     # reference sans fermer
```
Common types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`

Examples:
```bash
git commit -m "feat(audit): implement audit log API with filtering"
git commit -m "fix: catch ProtectedError on DELETE endpoints"
git commit -m "chore: update Docker config and README"
```

### Database Migrations
Apply migrations:
```bash
docker compose -f docker-compose.dev.yml run --rm backend python manage.py migrate
```