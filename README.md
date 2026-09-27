# TaskFlow API

[![CI](https://github.com/MigueIAngel/taskflow-api/actions/workflows/ci.yml/badge.svg)](https://github.com/MigueIAngel/taskflow-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

A task management REST API built with **FastAPI** and **SQLAlchemy 2.0**. Users sign up, get a JWT and manage their own projects and tasks, with filtering, sorting, pagination and per-project statistics.

**Live demo:** [Swagger UI](https://taskflow-api-demo-au9h.onrender.com/docs). Register a user, then use **Authorize** with its token.

> Hosted on Render's free plan: the first request after a period of inactivity can take up to a minute while the service wakes up. Demo data is reset on every restart.

## Features

- **JWT authentication**: register, log in (OAuth2 password flow) and fetch the current user
- **Projects**: CRUD, search by name, pagination and a stats endpoint (tasks by status, overdue tasks, completion rate)
- **Tasks**: CRUD nested under projects, filters by `status`, `priority` and text search, sorting by date, priority or title
- **Ownership checks**: a user can never read or modify another user's data
- **Typed end to end**: Pydantic v2 schemas, SQLAlchemy 2.0 `Mapped[]` models and a generic `Page[T]` response
- **Migrations** with Alembic
- **Interactive docs** at `/docs` (Swagger UI) and `/redoc`
- **Tests** with pytest against an in-memory SQLite database
- **CI** with GitHub Actions: Ruff, Alembic migrations against PostgreSQL and the pytest suite

## Tech stack

| Layer | Tools |
|---|---|
| Framework | FastAPI, Uvicorn |
| Data | SQLAlchemy 2.0, Alembic, PostgreSQL 16 (psycopg 3) |
| Auth | PyJWT, bcrypt |
| Config | pydantic-settings |
| Quality | pytest, httpx, Ruff |
| DevOps | Docker, docker-compose, GitHub Actions |

## Getting started

### With Docker (recommended)

```bash
docker compose up --build
```

The API is served at http://localhost:8000 and the docs at http://localhost:8000/docs. Migrations run automatically on startup.

### Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # adjust DATABASE_URL if needed
docker compose up -d db           # or use your own PostgreSQL
alembic upgrade head
uvicorn app.main:app --reload
```

### Running tests and linters

```bash
pytest
ruff check . && ruff format --check .
```

## API overview

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Get an access token (form: `username`, `password`) |
| `GET` | `/auth/me` | Current user |
| `GET` | `/projects?search=&page=&size=` | List own projects |
| `POST` | `/projects` | Create a project |
| `GET` `PATCH` `DELETE` | `/projects/{id}` | Read, update or delete a project |
| `GET` | `/projects/{id}/stats` | Task statistics |
| `GET` | `/projects/{id}/tasks?status=&priority=&search=&sort=&order=` | List tasks |
| `POST` | `/projects/{id}/tasks` | Create a task |
| `GET` `PATCH` `DELETE` | `/projects/{id}/tasks/{task_id}` | Read, update or delete a task |

### Example

```bash
curl -X POST localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","full_name":"Demo User","password":"demo12345"}'

TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d "username=demo@example.com&password=demo12345" | jq -r .access_token)

curl -X POST localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Portfolio"}'
```

## Project structure

```
app/
├── api/
│   ├── deps.py            # DB session and current-user dependencies
│   └── routes/            # auth, projects, tasks
├── core/
│   ├── config.py          # settings from environment
│   └── security.py        # bcrypt + JWT helpers
├── schemas/               # Pydantic models
├── db.py                  # engine, session, Base
├── models.py              # SQLAlchemy models
└── main.py                # app factory, CORS, routers
alembic/                   # migrations
tests/                     # pytest suite
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://taskflow:taskflow@localhost:5433/taskflow` | SQLAlchemy URL |
| `JWT_SECRET` | `change-me-in-production` | Secret used to sign tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

## License

MIT
