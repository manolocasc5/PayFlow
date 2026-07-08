"""Gestión de la conexión a SQLite y creación del esquema de tablas."""

import os
from collections.abc import AsyncGenerator

import aiosqlite

DB_PATH = os.environ.get("PAYFLOW_DB_PATH", "payflow.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS merchants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    status TEXT NOT NULL DEFAULT 'pending',
    description TEXT,
    customer_email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants (id)
);
"""


async def init_db() -> None:
    """Crea las tablas de la base de datos si todavía no existen."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependencia de FastAPI que entrega una conexión de base de datos por request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
