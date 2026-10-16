import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import appointments, doctors, patients

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("clinicflow")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema is owned by Alembic (run before Uvicorn in the container); this only seeds demo rows.
    if settings.seed_demo_data:
        from .seed import seed_if_empty

        seed_if_empty()
    log.info("%s %s started", settings.app_name, settings.app_version)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Clinic appointment scheduling API: doctors, patients and appointments.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)

app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)


@app.get("/", tags=["meta"])
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health", tags=["meta"])
@app.get("/api/health", tags=["meta"], include_in_schema=False)
def health():
    """Liveness: the process is up and serving HTTP. Deliberately does not touch the DB."""
    return {"status": "UP", "version": settings.app_version}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only accept traffic once the database answers."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        log.warning("Readiness check failed: %s", exc.__class__.__name__)
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "database": "unreachable"})
    return {"status": "READY", "database": "ok"}
