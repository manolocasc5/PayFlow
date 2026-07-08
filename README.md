# PayFlow API

API REST simplificada de procesamiento de pagos para una fintech ficticia. Proyecto educativo
construido con FastAPI y SQLite (sin ORM), pensado como base para practicar hooks de Claude Code.

## Stack

- Python 3.12+
- FastAPI
- SQLite vía `aiosqlite` (queries SQL directas, sin ORM)
- Pydantic v2 para validación
- pytest + httpx para tests
- uvicorn como servidor ASGI

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -e ".[dev]"
```

## Arrancar el servidor

```bash
python -m uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs
- Dashboard de prueba: http://localhost:8000/dashboard

## Ejecutar los tests

```bash
python -m pytest tests/ -v
```

## Endpoints

| Método | Ruta                        | Descripción                                   |
|--------|-----------------------------|------------------------------------------------|
| GET    | `/health`                   | Estado de la API                                |
| POST   | `/merchants`                | Crea un merchant (devuelve `api_key`)           |
| GET    | `/merchants`                | Lista merchants                                 |
| GET    | `/merchants/{id}`           | Detalle de un merchant                          |
| POST   | `/payments`                 | Crea un pago (requiere header `X-API-Key`)      |
| GET    | `/payments`                 | Lista los pagos del merchant (header `X-API-Key`)|
| GET    | `/payments/{id}`            | Detalle de un pago                              |
| PATCH  | `/payments/{id}/status`     | Cambia el estado de un pago                     |

### Transiciones de estado de pagos

```
pending -> completed
pending -> failed
completed -> refunded
```

Cualquier otra transición devuelve `400 Bad Request`.

## Autenticación

Los endpoints de pagos que requieren autenticación esperan el header `X-API-Key` con el
`api_key` devuelto al crear un merchant (formato `pk_` + 32 caracteres hexadecimales).

## Estructura del proyecto

```
payflow-api/
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS, montaje del frontend
│   ├── database.py          # Conexión SQLite y creación de tablas
│   ├── models.py            # Modelos Pydantic
│   ├── routers/             # Endpoints HTTP
│   └── services/            # Lógica de negocio
├── tests/                   # Tests con pytest + httpx
├── frontend/                # Dashboard HTML/CSS/JS vanilla
└── pyproject.toml
```
