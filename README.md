# AI Travel Concierge

AI-assisted travel stay browser and booking concierge (MVP learning project).

## Block 0 — how to run

Prerequisites: Docker, Python 3.11+, Node 20+, [`uv`](https://docs.astral.sh/uv/).

```bash
# 1. Postgres
docker compose up -d

# 2. Backend (from repo root)
cp .env.example .env
cd backend && uv sync --group dev && uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal; use Node 20+)
cd frontend && npm install && npm run dev
```

If `node -v` is still 16.x and you installed Homebrew `node@20`:

```bash
export PATH="$(brew --prefix node@20)/bin:$PATH"
```

- API: http://localhost:8000/health  
- UI: http://localhost:5173  

Later blocks add domain models, booking UI, the OpenAI concierge agent, and CI.
