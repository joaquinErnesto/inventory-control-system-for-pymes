# Baracoa Inventory Control System

An inventory management platform for small and medium-sized businesses (PyMEs), built around physical inventory batches, stock movement traceability, and real-time sales reporting.

The repository currently contains the **backend MVP** (FastAPI + SQLAlchemy + MySQL). The `frontend/` directory is reserved for the future client application.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.13 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (Declarative Base) |
| Database | MySQL 8.x (PyMySQL driver) |
| Validation | Pydantic v2 |
| Authentication | OAuth2 Password Flow + JWT (`python-jose`) |
| Password Hashing | Passlib + Bcrypt |
| Testing | Pytest + pytest-cov |
| Config | python-dotenv |

---

## Features

- **JWT authentication** with role-based access control (`admin` / `employee`).
- **Catalog management**: categories, products, suppliers, and customers, including search, sorting, and pagination helpers.
- **Batch-based inventory**: every stock arrival is a batch with its own cost, selling price, expiration date, and current quantity.
- **Sales processing** with automatic **FEFO/FIFO** stock deduction across batches.
- **Loss logging** for expired, damaged, stolen, or otherwise lost stock.
- **Full inventory transaction ledger** (`IN`, `OUT`, `LOSS`, `ADJUSTMENT`) with links to sales and losses.
- **Reports**: low stock, expiring inventory, sales performance, and per-batch audit trails.
- **Standardized API responses**, centralized exception handlers, request logging, and CORS configuration.

---

## Project Structure

```text
application/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Application entry point, middleware, health check
│   │   ├── config.py               # Environment loading and settings
│   │   ├── database.py             # SQLAlchemy engine, session, and Base
│   │   ├── security.py             # JWT creation/validation and role guards
│   │   ├── exceptions/             # Global exception handlers
│   │   ├── logging/                # Application logger
│   │   ├── models/                 # SQLAlchemy models (database schema)
│   │   ├── routers/                # HTTP endpoints by domain
│   │   ├── schemas/                # Pydantic request/response schemas and enums
│   │   ├── services/               # Business logic (sales, batches, losses)
│   │   └── utils/                  # Pagination and query sorting helpers
│   ├── scripts/
│   │   ├── seed_database.py        # Development data seeder
│   │   └── seeders/                # Per-entity seeders
│   ├── tests/                      # Unit and integration tests
│   ├── pytest.ini
│   └── requirements.txt
└── frontend/                       # Reserved for the client application
```

---

## Data Model

The core schema is defined in `backend/app/models/core.py`:

- `User` — credentials, role, and audit links.
- `Category` — product taxonomy.
- `Supplier` — vendor records.
- `Customer` — consumer records.
- `Product` — global item definition, SKU/barcode, unit of measure, and minimum stock threshold.
- `InventoryBatch` — physical stock arrival with cost, selling price, expiration date, and remaining quantity.
- `Sale` / `SaleItem` — sales header and line items, each tied to a specific batch.
- `LossLog` — recorded stock losses with reason and quantity.
- `InventoryTransaction` — immutable ledger of every stock change.

---

## API Overview

All application routes are prefixed with `/api/v1`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/token` | Obtain a JWT access token |
| `GET` | `/` | API welcome message |
| `GET` | `/health/db` | Database connectivity check |
| `GET/POST` | `/categories` | List and create categories |
| `GET/PUT/DELETE` | `/categories/{category_id}` | Retrieve, update, delete a category |
| `GET/POST` | `/suppliers` | List and create suppliers |
| `GET` | `/suppliers/search/` | Search suppliers |
| `GET/PUT/DELETE` | `/suppliers/{supplier_id}` | Retrieve, update, delete a supplier |
| `GET/POST` | `/products` | List and create products |
| `GET` | `/products/search/` | Search products |
| `GET/PUT/DELETE` | `/products/{product_id}` | Retrieve, update, delete a product |
| `GET/POST` | `/customers` | List and create customers |
| `GET` | `/customers/search/` | Search customers |
| `GET/PUT/DELETE` | `/customers/{customer_id}` | Retrieve, update, delete a customer |
| `GET/POST` | `/users` | List and create users (admin only) |
| `GET` | `/users/me` | Current authenticated user |
| `GET` | `/users/search/` | Search users |
| `GET/PUT/DELETE` | `/users/{user_id}` | Retrieve, update, delete a user |
| `PUT` | `/users/{user_id}/password` | Change a user password |
| `GET/POST` | `/batches` | List and register inventory batches |
| `GET/DELETE` | `/batches/{batch_id}` | Retrieve or delete a batch |
| `GET/POST` | `/sales` | List and process sales (FEFO/FIFO deduction) |
| `GET` | `/sales/{sale_id}` | Retrieve a sale with its items |
| `GET/POST` | `/losses` | List and register stock losses |
| `GET` | `/losses/{loss_id}` | Retrieve a loss record |
| `GET` | `/inventory-transactions` | List ledger transactions |
| `GET` | `/inventory-transactions/{transaction_id}` | Retrieve a transaction |
| `GET` | `/inventory-transactions/summary/overview` | Transaction summary |
| `GET` | `/inventory-transactions/today/activity` | Today's inventory activity |
| `GET` | `/reports/low-stock` | Products at or below minimum threshold |
| `GET` | `/reports/expiring-soon` | Batches nearing expiration |
| `GET` | `/reports/sales-performance` | Sales performance metrics |
| `GET` | `/reports/batch-audit/{batch_id}` | Full audit trail for a batch |

Interactive documentation is available at `/docs` and the OpenAPI schema at `/openapi.json` once the server is running.

---

## Getting Started

### Prerequisites

- Python 3.13+
- MySQL 8.x running and reachable
- A database created for the application (e.g. `inventory_db`)

### 1. Install dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure the environment

Create `backend/.env` with the following variables:

```env
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>
SECRET_KEY=<long-random-secret>
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

> `DATABASE_URL` and `SECRET_KEY` are required; the application raises an error at startup if either is missing. Real credentials must never be committed to version control.

For tests, `backend/.env.test` is loaded automatically by `tests/conftest.py` and must define the same variables pointing to an isolated test database.

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup via the SQLAlchemy metadata. The API will be available at `http://127.0.0.1:8000`, with Swagger UI at `http://127.0.0.1:8000/docs`.

### 4. Seed development data (optional)

```bash
python scripts/seed_database.py
```

The seeder is idempotent: it populates users, categories, suppliers, customers, products, batches, sales, and loss logs while skipping records that already exist.

---

## Testing

The test suite lives in `backend/tests` and covers routers, services, schemas, security, utilities, exception handlers, and application startup. Each test runs against a clean database created and dropped by the `db` fixture.

```bash
cd backend
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

The HTML coverage report is generated in `backend/htmlcov/`.

---

## Response Format

Successful responses follow a consistent envelope defined in `backend/app/schemas/responses.py`:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {}
}
```

Errors are normalized by the global exception handlers, returning `success: false` with a `message` and, for validation failures, a list of field-level `errors`.

---

## Status

This is an MVP under active development. The backend API and its test suite are being expanded, and the frontend client has not been implemented yet.
