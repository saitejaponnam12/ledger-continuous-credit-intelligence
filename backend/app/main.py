"""
LEDGER — FastAPI Application Entry Point
Assembles all routers, middleware, and startup logic.
"""
from __future__ import annotations

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import create_all_tables

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    log.info("ledger_startup", version=settings.app_version, env=settings.app_env)

    # Create DB tables if they don't exist (development convenience)
    if settings.app_env in ("development", "test"):
        await create_all_tables()
        log.info("db_tables_ready")

    # Preload sentence-transformers model (avoids cold start on first request)
    if settings.app_env != "test":
        try:
            from app.rag.retriever import get_embedding_model
            get_embedding_model()
            log.info("embedding_model_loaded", model=settings.embedding_model)
        except Exception as e:
            log.warning("embedding_model_load_failed", error=str(e))

    # Check LLM availability
    try:
        from app.copilot.providers import get_llm_provider
        provider = get_llm_provider()
        log.info("llm_provider_ready", provider=provider.__class__.__name__)
    except Exception as e:
        log.warning("llm_provider_check_failed", error=str(e))

    yield

    log.info("ledger_shutdown")


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="LEDGER — Continuous Credit Intelligence",
    description=(
        "AI-powered underwriting platform using Financial Digital Twins, "
        "XGBoost decision engine, SHAP explainability, and RAG-powered copilot. "
        "Built for the One Synchrony Hackathon 2026."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# Rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — explicit allowlist, no wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ── Import routers ────────────────────────────────────────────────────────
from app.api import auth, applications, events, copilot, demo, health

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(copilot.router, prefix="/api/v1/copilot", tags=["Copilot"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["Demo"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "product": "LEDGER — Continuous Credit Intelligence",
        "version": settings.app_version,
        "thesis": "UNKNOWN ≠ UNTRUSTWORTHY",
        "disclaimer": (
            "This prototype uses synthetic data and is intended for decision support, "
            "not autonomous lending. Human review remains the final authority."
        ),
    }
