"""FastAPI entrypoint — authenticated skill-gap platform."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, analyze, auth, health, jobs, roles, sample_jds
from app.core.config import settings
from app.startup import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-style academic platform: resume skill-gap analysis with hard eligibility "
        "gates (CGPA, experience, location), selection-likelihood scoring, coaching summaries, "
        "learning roadmaps, what-if simulation, user accounts, and an admin console."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(roles.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(sample_jds.router, prefix=settings.api_prefix)
app.include_router(analyze.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_prefix,
    }
