# AI Travel Concierge

AI-assisted travel stay browser and booking concierge (MVP learning project).

## Block 0 — how to run

Prerequisites: Docker, Python 3.11+, Node 20+, `[uv](https://docs.astral.sh/uv/)`.

```bash
export PATH="$PWD/.venv/bin:$(brew --prefix node@20)/bin:$PATH"
```

### Architecture


| Piece    | Tech                                   | Role                                             |
| -------- | -------------------------------------- | ------------------------------------------------ |
| Database | Postgres (Docker)                      | Persistent data                                  |
| Backend  | **FastAPI** app served by **Uvicorn**  | JSON API (`/health`, later booking + chat)       |
| Frontend | React + TypeScript via **Vite** (Node) | Browser UI; Vite compiles TS/JSX and hot-reloads |


FastAPI is the API framework; Uvicorn is the HTTP server that runs it (`uvicorn app.main:app`). The React UI is a separate SPA, so it uses a Node/Vite dev server rather than a single FastAPI `GET /` HTML page—that keeps the TypeScript toolchain, client routing, and hot reload usable while FastAPI stays focused on the API.

### Startup


| Piece                         | Command                                                                                                                     | Port     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------- |
| Database (Postgres)           | `docker compose up -d`                                                                                                      | **5432** |
| Backend (FastAPI via Uvicorn) | `cp .env.example .env` (once), then `cd backend && uv sync --group dev && uv run uvicorn app.main:app --reload --port 8000` | **8000** |
| Frontend (Vite React)         | `cd frontend && npm install && npm run dev`                                                                                 | **5173** |


Run the backend and frontend each in their own terminal (the database can stay in the background).

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- UI: [http://localhost:5173](http://localhost:5173)
- UI → API proxy: the browser calls `/api/...` on **5173**; Vite forwards to FastAPI on **8000**



### Shutdown


| Piece    | Command                                                                  |
| -------- | ------------------------------------------------------------------------ |
| Frontend | `Ctrl+C` in the `npm run dev` terminal                                   |
| Backend  | `Ctrl+C` in the `uvicorn` terminal                                       |
| Database | `docker compose down` (add `-v` only if you also want to delete DB data) |


Later blocks add domain models, booking UI, the OpenAI concierge agent, and CI.