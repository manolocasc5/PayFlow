"""Tests de creación, listado y transición de estados de pagos."""

from httpx import AsyncClient


async def _create_merchant(client: AsyncClient) -> dict:
    response = await client.post(
        "/merchants", json={"name": "Test Merchant", "email": "merchant@example.com"}
    )
    return response.json()


async def test_create_payment_with_valid_api_key(client: AsyncClient) -> None:
    """POST /payments con un api_key válido debe crear el pago en estado 'pending'."""
    merchant = await _create_merchant(client)

    response = await client.post(
        "/payments",
        json={
            "amount": 49.99,
            "currency": "EUR",
            "description": "Suscripción mensual",
            "customer_email": "cliente@example.com",
        },
        headers={"X-API-Key": merchant["api_key"]},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["merchant_id"] == merchant["id"]
    assert data["amount"] == 49.99


async def test_create_payment_without_api_key_returns_401(client: AsyncClient) -> None:
    """POST /payments sin header X-API-Key debe devolver 401."""
    response = await client.post(
        "/payments",
        json={
            "amount": 10.0,
            "currency": "EUR",
            "customer_email": "cliente@example.com",
        },
    )

    assert response.status_code == 401


async def test_create_payment_with_invalid_api_key_returns_401(client: AsyncClient) -> None:
    """POST /payments con un api_key inexistente debe devolver 401."""
    response = await client.post(
        "/payments",
        json={
            "amount": 10.0,
            "currency": "EUR",
            "customer_email": "cliente@example.com",
        },
        headers={"X-API-Key": "pk_no_existe"},
    )

    assert response.status_code == 401


async def test_list_payments_for_merchant(client: AsyncClient) -> None:
    """GET /payments debe listar únicamente los pagos del merchant autenticado."""
    merchant = await _create_merchant(client)
    headers = {"X-API-Key": merchant["api_key"]}

    await client.post(
        "/payments",
        json={"amount": 20.0, "currency": "EUR", "customer_email": "a@example.com"},
        headers=headers,
    )
    await client.post(
        "/payments",
        json={"amount": 30.0, "currency": "EUR", "customer_email": "b@example.com"},
        headers=headers,
    )

    response = await client.get("/payments", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_valid_status_transition(client: AsyncClient) -> None:
    """PATCH /payments/{id}/status debe permitir la transición pending -> completed."""
    merchant = await _create_merchant(client)
    create_response = await client.post(
        "/payments",
        json={"amount": 15.0, "currency": "EUR", "customer_email": "a@example.com"},
        headers={"X-API-Key": merchant["api_key"]},
    )
    payment_id = create_response.json()["id"]

    response = await client.patch(f"/payments/{payment_id}/status", json={"status": "completed"})

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_invalid_status_transition_returns_400(client: AsyncClient) -> None:
    """PATCH /payments/{id}/status con una transición no permitida debe devolver 400."""
    merchant = await _create_merchant(client)
    create_response = await client.post(
        "/payments",
        json={"amount": 15.0, "currency": "EUR", "customer_email": "a@example.com"},
        headers={"X-API-Key": merchant["api_key"]},
    )
    payment_id = create_response.json()["id"]

    # pending -> refunded no es una transición válida
    response = await client.patch(f"/payments/{payment_id}/status", json={"status": "refunded"})

    assert response.status_code == 400
