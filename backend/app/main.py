from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import engine

app = FastAPI(title="AI Travel Concierge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    database = "down"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "up"
    except Exception:
        database = "down"

    status = "ok" if database == "up" else "degraded"
    return {"status": status, "database": database}
