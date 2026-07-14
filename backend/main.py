"""
KSP Crime Analytics — FastAPI Application Entry Point
=====================================================
Main application file that wires together all routers,
middleware, and configuration.

Run with:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import cases, analytics, lookups, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    print("🚀 KSP Crime Analytics API starting...")
    print(f"📊 Database: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
    yield
    print("🛑 KSP Crime Analytics API shutting down...")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(cases.router)
app.include_router(analytics.router)
app.include_router(lookups.router)
app.include_router(chat.router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }


@app.get("/api", tags=["Health"])
def api_info():
    """API information and available endpoints."""
    return {
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "endpoints": {
            "cases": "/api/cases",
            "case_detail": "/api/cases/{case_id}",
            "analytics_overview": "/api/analytics/overview",
            "crime_trends": "/api/analytics/crime-trends",
            "crime_by_district": "/api/analytics/crime-by-district",
            "crime_by_type": "/api/analytics/crime-by-type",
            "status_distribution": "/api/analytics/status-distribution",
            "hotspots": "/api/analytics/hotspots",
            "repeat_offenders": "/api/analytics/repeat-offenders",
            "age_distribution": "/api/analytics/age-distribution",
            "lookups_districts": "/api/lookups/districts",
            "lookups_stations": "/api/lookups/stations",
            "lookups_crime_heads": "/api/lookups/crime-heads",
            "lookups_case_statuses": "/api/lookups/case-statuses",
            "chat": "/api/chat",
            "build_index": "/api/chat/build-index",
            "docs": "/docs",
        },
    }
