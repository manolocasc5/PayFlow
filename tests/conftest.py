"""Fixtures compartidas: cliente HTTP de test y base de datos temporal aislada por test."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import database


@pytest_asyncio.fixture
async def client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP asíncrono contra la app, con una base de datos SQLite temporal por test."""
    database.DB_PATH = str(tmp_path / "test_payflow.db")
    await database.init_db()

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
