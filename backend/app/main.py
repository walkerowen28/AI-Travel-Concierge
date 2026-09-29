import socket

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.errors import ConflictError, NotFoundError, ValidationError
from app.routers.chat import router as chat_router
from app.routers.properties import router as properties_router
from app.routers.reservations import router as reservations_router

settings = get_settings()
# In Kubernetes the Downward API sets POD_NAME; elsewhere the container hostname is close enough.
SERVED_BY = settings.pod_name or socket.gethostname()

app = FastAPI(title="AI Travel Concierge")

app.include_router(properties_router)
app.include_router(reservations_router)
app.include_router(chat_router)


@app.exception_handler(NotFoundError)
def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(ValidationError)
def validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


@app.middleware("http")
async def served_by_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Api-Pod"] = SERVED_BY
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Api-Pod"],
)


def _database_up() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health")
def health() -> dict[str, str]:
    database = "up" if _database_up() else "down"
    status = "ok" if database == "up" else "degraded"
    return {"status": status, "database": database, "pod": SERVED_BY}


@app.get("/health/live")
def health_live() -> dict[str, str]:
    # Liveness must not depend on Postgres, or a DB outage restarts every API pod.
    return {"status": "ok", "pod": SERVED_BY}


@app.get("/health/ready")
def health_ready() -> JSONResponse:
    if _database_up():
        return JSONResponse({"status": "ready", "database": "up", "pod": SERVED_BY})
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "database": "down", "pod": SERVED_BY},
    )
