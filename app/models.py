"""Modelos Pydantic para validación de requests y forma de las responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

PaymentStatus = Literal["pending", "completed", "failed", "refunded", "partially_refunded"]
MerchantStatus = Literal["active", "suspended"]


class MerchantCreate(BaseModel):
    """Datos requeridos para dar de alta un nuevo merchant."""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=EMAIL_PATTERN)


class MerchantOut(BaseModel):
    """Representación pública de un merchant (sin api_key)."""

    id: str
    name: str
    email: str
    status: MerchantStatus
    created_at: datetime


class MerchantCreateResponse(MerchantOut):
    """Respuesta al crear un merchant, incluye el api_key generado una única vez."""

    api_key: str


class PaymentCreate(BaseModel):
    """Datos requeridos para crear un nuevo pago."""

    amount: float = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=500)
    customer_email: str = Field(pattern=EMAIL_PATTERN)


class PaymentOut(BaseModel):
    """Representación de un pago."""

    id: str
    merchant_id: str
    amount: float
    currency: str
    status: PaymentStatus
    description: str | None
    customer_email: str
    refunded_amount: float
    created_at: datetime
    updated_at: datetime


class PaymentStatusUpdate(BaseModel):
    """Payload para cambiar el estado de un pago."""

    status: Literal["completed", "failed", "refunded"]


class PartialRefundRequest(BaseModel):
    """Payload para solicitar el reembolso parcial de un pago."""

    amount: float = Field(gt=0)


class HealthResponse(BaseModel):
    """Respuesta del health check de la API."""

    status: str
    version: str
    timestamp: datetime
