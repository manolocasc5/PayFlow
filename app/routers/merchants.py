"""Endpoints CRUD de merchants."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import MerchantCreate, MerchantCreateResponse, MerchantOut
from app.services import merchant_service

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("", response_model=MerchantCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    payload: MerchantCreate, db: aiosqlite.Connection = Depends(get_db)
) -> dict:
    """Crea un nuevo merchant y devuelve sus datos junto con el api_key generado."""
    return await merchant_service.create_merchant(db, payload.name, payload.email)


@router.get("", response_model=list[MerchantOut])
async def list_merchants(db: aiosqlite.Connection = Depends(get_db)) -> list[dict]:
    """Lista todos los merchants registrados."""
    return await merchant_service.list_merchants(db)


@router.get("/{merchant_id}", response_model=MerchantOut)
async def get_merchant(merchant_id: str, db: aiosqlite.Connection = Depends(get_db)) -> dict:
    """Obtiene el detalle de un merchant por su ID. Devuelve 404 si no existe."""
    merchant = await merchant_service.get_merchant_by_id(db, merchant_id)
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant no encontrado")
    return merchant
