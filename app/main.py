"""Punto de entrada de la aplicación FastAPI de PayFlow."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import health, merchants, payments

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa el esquema de la base de datos al arrancar la aplicación."""
    await init_db()
    yield


app = FastAPI(
    title="PayFlow API",
    description="API REST simplificada de procesamiento de pagos (proyecto educativo)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(merchants.router)
app.include_router(payments.router)

if FRONTEND_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")
