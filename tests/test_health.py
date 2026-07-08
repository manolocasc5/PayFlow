"""Tests del endpoint de health check."""

from httpx import AsyncClient


async def test_health_check_returns_200(client: AsyncClient) -> None:
    """GET /health debe responder 200 con status 'ok' y la versión de la API."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
