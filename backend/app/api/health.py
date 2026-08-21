"""LEDGER — Health Check Router"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "demo_mode": settings.demo_mode,
    }
