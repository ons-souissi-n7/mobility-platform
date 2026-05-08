## How to run

Start the development stack:

```powershell
docker compose -p mobility-dev -f docker-compose.dev.yml up --build
```

Stop the development stack:

```powershell
docker compose -p mobility-dev -f docker-compose.dev.yml down
```

Run Django management commands:

```powershell
docker compose -p mobility-dev -f docker-compose.dev.yml run --rm backend python manage.py COMMAND
```

For example, create a Django app named `reference`:

```powershell
docker compose -p mobility-dev -f docker-compose.dev.yml run --rm backend python manage.py startapp reference
```

The Django project already exists in `backend/config`, so do not run
`django-admin startproject config .` again unless you are recreating the backend
from scratch.

PostgreSQL is exposed on `localhost:5433` by default to avoid conflicts with a
local PostgreSQL server already using `5432`.
