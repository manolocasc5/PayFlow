"""Endpoints CRUD de pagos, protegidos mediante el header X-API-Key."""

from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.database import get_db
from app.models import PartialRefundRequest, PaymentCreate, PaymentOut, PaymentStatusUpdate
from app.services import merchant_service, payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


async def get_current_merchant(
    x_api_key: str | None = Header(default=None),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Valida el header X-API-Key y devuelve el merchant asociado. Lanza 401 si no es válido."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta el header X-API-Key"
        )
    merchant = await merchant_service.get_merchant_by_api_key(db, x_api_key)
    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key inválido"
        )
    return merchant


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    merchant: dict = Depends(get_current_merchant),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Crea un nuevo pago en estado 'pending' para el merchant autenticado."""
    return await payment_service.create_payment(
        db,
        merchant_id=merchant["id"],
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        customer_email=payload.customer_email,
    )


@router.get("", response_model=list[PaymentOut])
async def list_payments(
    merchant: dict = Depends(get_current_merchant),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    """Lista los pagos del merchant autenticado mediante X-API-Key."""
    return await payment_service.list_payments_by_merchant(db, merchant["id"])


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(payment_id: str, db: aiosqlite.Connection = Depends(get_db)) -> dict:
    """Obtiene el detalle de un pago por su ID. Devuelve 404 si no existe."""
    payment = await payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    return payment


@router.patch("/{payment_id}/status", response_model=PaymentOut)
async def update_payment_status(
    payment_id: str,
    payload: PaymentStatusUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Cambia el estado de un pago validando que la transición sea permitida."""
    payment = await payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    if not payment_service.is_valid_transition(payment["status"], payload.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transición de estado inválida: {payment['status']} -> {payload.status}",
        )

    updated = await payment_service.update_payment_status(db, payment_id, payload.status)
    return updated


@router.post("/{payment_id}/partial-refund", response_model=PaymentOut)
async def partial_refund_payment(
    payment_id: str,
    payload: PartialRefundRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Aplica un reembolso parcial a un pago. 404 si no existe, 400 si el importe o el estado no son válidos."""
    payment = await payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    try:
        updated = await payment_service.partial_refund_payment(db, payment_id, payload.amount)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return updated
