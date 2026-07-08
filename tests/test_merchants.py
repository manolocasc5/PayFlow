"""Tests de creación, listado y detalle de merchants."""

from httpx import AsyncClient


async def test_create_merchant_returns_api_key(client: AsyncClient) -> None:
    """POST /merchants debe crear un merchant y devolver su api_key."""
    response = await client.post(
        "/merchants", json={"name": "Acme Store", "email": "acme@example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Store"
    assert data["email"] == "acme@example.com"
    assert data["status"] == "active"
    assert data["api_key"].startswith("pk_")
    assert len(data["api_key"]) == len("pk_") + 32
    assert "id" in data


async def test_list_merchants(client: AsyncClient) -> None:
    """GET /merchants debe listar todos los merchants creados."""
    await client.post("/merchants", json={"name": "Merchant A", "email": "a@example.com"})
    await client.post("/merchants", json={"name": "Merchant B", "email": "b@example.com"})

    response = await client.get("/merchants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {m["name"] for m in data}
    assert names == {"Merchant A", "Merchant B"}
    assert "api_key" not in data[0]


async def test_get_merchant_by_id(client: AsyncClient) -> None:
    """GET /merchants/{id} debe devolver el detalle de un merchant existente."""
    create_response = await client.post(
        "/merchants", json={"name": "Merchant C", "email": "c@example.com"}
    )
    merchant_id = create_response.json()["id"]

    response = await client.get(f"/merchants/{merchant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == merchant_id
    assert data["name"] == "Merchant C"


async def test_get_merchant_not_found(client: AsyncClient) -> None:
    """GET /merchants/{id} con un ID inexistente debe devolver 404."""
    response = await client.get("/merchants/id-que-no-existe")

    assert response.status_code == 404
