# AI Travel Concierge

AI-assisted travel stay browser and booking concierge (MVP learning project).

## Architecture

Three processes, each its own container. That is the shape a later Kubernetes cluster would use: one Deployment per service, an Ingress in front of `web`, and Postgres either in-cluster or a managed database.

| Piece | Image | Role | Host port |
|-------|-------|------|-----------|
| Database | `postgres:16` | Persistent data | **5432** |
| API | `backend/Dockerfile` (FastAPI + Uvicorn) | JSON API (`/health`, later booking + chat) | **8000** |
| Web | `frontend/Dockerfile` (built React app served by nginx) | Browser UI. nginx proxies `/api` to the `api` service | **8080** |

FastAPI is the API framework; Uvicorn is the HTTP server inside the API container. The React UI is a built static site, not Vite's dev server, so the web container does not need Node at runtime.

The browser always calls `/api/...`. Local Vite and container nginx both strip that prefix before FastAPI sees the path (`/api/health` becomes `/health`).

## Prerequisites

Docker. For hot-reload development on the host you also need Python 3.11+, Node 20+, and [`uv`](https://docs.astral.sh/uv/).

```bash
export PATH="$PWD/.venv/bin:$(brew --prefix node@20)/bin:$PATH"
cp .env.example .env
```

## Full stack in containers

Stop any host process already bound to ports 8000 or 5173, then:

```bash
docker compose up -d --build
```

- UI: http://localhost:8080
- API: http://localhost:8000/health
- UI → API: http://localhost:8080/api/health

```bash
docker compose down          # stop containers
docker compose down -v       # also delete Postgres data
```

## Host dev (hot reload)

Use this when you are changing code. Only Postgres stays in Docker.

```bash
docker compose up -d db

# terminal 2
cd backend && uv sync --group dev && uv run uvicorn app.main:app --reload --port 8000

# terminal 3
cd frontend && npm install && npm run dev
```

| Piece | Shutdown |
|-------|----------|
| Frontend | `Ctrl+C` in the `npm run dev` terminal |
| Backend | `Ctrl+C` in the `uvicorn` terminal |
| Database | `docker compose stop db` |

- Health: http://localhost:8000/health
- UI: http://localhost:5173
- Vite proxy: `/api` on **5173** forwards to FastAPI on **8000**

Do not run host Uvicorn and the `api` container at the same time. Both want port 8000.

## Domain data

From `backend/`, with Postgres running:

```bash
uv sync --group dev
uv run alembic upgrade head
uv run python -m app.seed
```

That loads demo guest Alex (`user id` 1), about two dozen properties, and one upcoming reservation. Seed skips itself if properties already exist.

### UI (Block 2)

| Route | What it does |
|-------|----------------|
| `/` | Browse + filters |
| `/properties/:id` | Detail, house rules, nearby, book form |
| `/reservations` | Cancel, extend, report issue |

- Vite: http://localhost:5173
- Container web: http://localhost:8080
- API docs: http://localhost:8000/docs

If the API is the Compose container, rebuild it after backend changes: `docker compose up -d --build api`. Rebuild the web image after frontend changes: `docker compose up -d --build web`. Migrations still run from the host against the published Postgres port.

Later blocks add the OpenAI concierge agent and CI.
