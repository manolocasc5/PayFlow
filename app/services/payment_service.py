"""Lógica de negocio relacionada con los pagos, incluyendo las transiciones de estado."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import aiosqlite

# Transiciones de estado permitidas: estado actual -> conjunto de estados destino válidos.
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"completed", "failed"},
    "completed": {"refunded"},
    "failed": set(),
    "refunded": set(),
    "partially_refunded": set(),
}

# Estados desde los que un pago admite reembolso (total o parcial).
REFUNDABLE_STATUSES = {"completed", "partially_refunded"}


async def create_payment(
    db: aiosqlite.Connection,
    merchant_id: str,
    amount: float,
    currency: str,
    description: str | None,
    customer_email: str,
) -> dict[str, Any]:
    """Crea un nuevo pago en estado 'pending' asociado a un merchant."""
    payment_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    await db.execute(
        """
        INSERT INTO payments
            (id, merchant_id, amount, currency, status, description, customer_email, refunded_amount, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'pending', ?, ?, 0, ?, ?)
        """,
        (payment_id, merchant_id, amount, currency, description, customer_email, now, now),
    )
    await db.commit()

    return {
        "id": payment_id,
        "merchant_id": merchant_id,
        "amount": amount,
        "currency": currency,
        "status": "pending",
        "description": description,
        "customer_email": customer_email,
        "refunded_amount": 0.0,
        "created_at": now,
        "updated_at": now,
    }


async def list_payments_by_merchant(db: aiosqlite.Connection, merchant_id: str) -> list[dict[str, Any]]:
    """Devuelve todos los pagos de un merchant, ordenados por fecha de creación descendente."""
    cursor = await db.execute(
        "SELECT * FROM payments WHERE merchant_id = ? ORDER BY created_at DESC",
        (merchant_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_payment_by_id(db: aiosqlite.Connection, payment_id: str) -> dict[str, Any] | None:
    """Busca un pago por su ID. Devuelve None si no existe."""
    cursor = await db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_payments_by_email(db: aiosqlite.Connection, customer_email: str) -> list[dict[str, Any]]:
    """Busca todos los pagos asociados a un email de cliente, ordenados por fecha de creación descendente."""
    cursor = await db.execute(
        "SELECT * FROM payments WHERE customer_email = ? ORDER BY created_at DESC",
        (customer_email,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """Comprueba si la transición de current_status a new_status está permitida."""
    return new_status in VALID_TRANSITIONS.get(current_status, set())


async def update_payment_status(
    db: aiosqlite.Connection, payment_id: str, new_status: str
) -> dict[str, Any] | None:
    """Actualiza el estado de un pago tras validar la transición. Devuelve el pago actualizado.

    Si el nuevo estado es 'refunded', también fija refunded_amount al importe total del pago,
    para que quede consistente con los reembolsos aplicados vía partial_refund_payment.
    """
    now = datetime.now(UTC).isoformat()
    if new_status == "refunded":
        await db.execute(
            "UPDATE payments SET status = ?, refunded_amount = amount, updated_at = ? WHERE id = ?",
            (new_status, now, payment_id),
        )
    else:
        await db.execute(
            "UPDATE payments SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, payment_id),
        )
    await db.commit()
    return await get_payment_by_id(db, payment_id)


async def partial_refund_payment(
    db: aiosqlite.Connection, payment_id: str, amount: float
) -> dict[str, Any] | None:
    """Aplica un reembolso parcial a un pago. Devuelve None si el pago no existe.

    Lanza ValueError si el pago no está en un estado reembolsable o si el importe
    solicitado supera el saldo pendiente de reembolso. Cuando el saldo reembolsado
    alcanza el importe total del pago, el estado pasa a 'refunded'; en caso
    contrario, a 'partially_refunded'.
    """
    payment = await get_payment_by_id(db, payment_id)
    if payment is None:
        return None

    if payment["status"] not in REFUNDABLE_STATUSES:
        raise ValueError(f"No se puede reembolsar un pago en estado '{payment['status']}'")

    refundable_balance = payment["amount"] - payment["refunded_amount"]
    if amount > refundable_balance:
        raise ValueError(
            f"El importe a reembolsar ({amount}) supera el saldo disponible ({refundable_balance})"
        )

    new_refunded_amount = payment["refunded_amount"] + amount
    new_status = "refunded" if new_refunded_amount >= payment["amount"] else "partially_refunded"
    now = datetime.now(UTC).isoformat()

    await db.execute(
        "UPDATE payments SET refunded_amount = ?, status = ?, updated_at = ? WHERE id = ?",
        (new_refunded_amount, new_status, now, payment_id),
    )
    await db.commit()
    return await get_payment_by_id(db, payment_id)
