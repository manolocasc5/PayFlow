"""Lógica de negocio relacionada con los merchants."""

import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import aiosqlite


def _generate_api_key() -> str:
    """Genera un api_key con el formato 'pk_' seguido de 32 caracteres hexadecimales."""
    return "pk_" + secrets.token_hex(16)


async def create_merchant(db: aiosqlite.Connection, name: str, email: str) -> dict[str, Any]:
    """Crea un nuevo merchant con un api_key generado aleatoriamente y estado 'active'."""
    merchant_id = str(uuid4())
    api_key = _generate_api_key()
    created_at = datetime.now(UTC).isoformat()

    await db.execute(
        """
        INSERT INTO merchants (id, name, email, api_key, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (merchant_id, name, email, api_key, "active", created_at),
    )
    await db.commit()

    return {
        "id": merchant_id,
        "name": name,
        "email": email,
        "api_key": api_key,
        "status": "active",
        "created_at": created_at,
    }


async def list_merchants(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    """Devuelve todos los merchants registrados, ordenados por fecha de creación descendente."""
    cursor = await db.execute("SELECT * FROM merchants ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_merchant_by_id(db: aiosqlite.Connection, merchant_id: str) -> dict[str, Any] | None:
    """Busca un merchant por su ID. Devuelve None si no existe."""
    cursor = await db.execute("SELECT * FROM merchants WHERE id = ?", (merchant_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_merchant_by_api_key(db: aiosqlite.Connection, api_key: str) -> dict[str, Any] | None:
    """Busca un merchant activo por su api_key. Devuelve None si no existe o no coincide."""
    cursor = await db.execute("SELECT * FROM merchants WHERE api_key = ?", (api_key,))
    row = await cursor.fetchone()
    return dict(row) if row else None
