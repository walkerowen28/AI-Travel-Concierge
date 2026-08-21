# AI Travel Concierge

AI-assisted travel stay browser and booking concierge (MVP learning project).

## Block 0 — how to run

Prerequisites: Docker, Python 3.11+, Node 20+, [`uv`](https://docs.astral.sh/uv/).

This repo’s root `.venv` includes `uv` if you don’t have it globally:

```bash
export PATH="$PWD/.venv/bin:$(brew --prefix node@20)/bin:$PATH"
```

```bash
# 1. Postgres
docker compose up -d

# 2. Backend (from repo root)
cp .env.example .env
cd backend && uv sync --group dev && uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal; Node 20+)
cd frontend && npm install && npm run dev
```

- API: http://localhost:8000/health  
- UI: http://localhost:5173  

Later blocks add domain models, booking UI, the OpenAI concierge agent, and CI.
