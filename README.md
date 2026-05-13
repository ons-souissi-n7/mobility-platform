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

# Load MoveOn API fake data
docker compose -f docker-compose.dev.yml exec backend python manage.py loaddata fake-moveon-api/data/institutions.json
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
