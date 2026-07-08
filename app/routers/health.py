"""Endpoint de health check."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.models import HealthResponse

router = APIRouter(tags=["health"])

API_VERSION = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Comprueba que la API está operativa y devuelve la versión y el timestamp actual."""
    return HealthResponse(status="ok", version=API_VERSION, timestamp=datetime.now(UTC))
