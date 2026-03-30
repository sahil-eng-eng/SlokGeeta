# Teaching Guide — ShlokVault Backend Architecture

This document explains the codebase to new developers and junior engineers.

---

## Project Layout

```
shlok-backend-recreated/
├── app/
│   ├── main.py                 ← FastAPI application entry point
│   ├── core/                   ← Framework-level plumbing
│   │   ├── config.py           ← Environment settings (Pydantic BaseSettings)
│   │   ├── database.py         ← Async SQLAlchemy engine + session
│   │   ├── security.py         ← Password hashing, JWT creation/decoding
│   │   ├── dependencies.py     ← FastAPI Depends() for auth
│   │   ├── handlers.py         ← Global exception → HTTP response converters
│   │   └── responses.py        ← ApiResponse[T] generic wrapper
│   ├── constants/              ← All hardcoded values live here
│   │   ├── enums.py            ← Visibility, AuthProvider, etc.
│   │   └── messages.py         ← Every user-facing string
│   ├── exceptions/             ← Typed error hierarchy
│   │   ├── base.py             ← ShlokVaultException + generic types
│   │   ├── auth.py             ← Auth-specific errors
│   │   ├── books.py            ← Book-specific errors
│   │   └── shloks.py           ← Shlok-specific errors
│   ├── models/                 ← SQLAlchemy ORM models
│   │   ├── base.py             ← Base class with id, created_at, updated_at
│   │   ├── user.py             ← User + RefreshToken
│   │   ├── book.py             ← Book
│   │   ├── shlok.py            ← Shlok + ShlokCrossReference
│   │   └── permission.py       ← Permission (entity-level access)
│   ├── schemas/                ← Pydantic request/response models
│   │   ├── auth.py
│   │   ├── books.py
│   │   └── shloks.py
│   ├── repositories/           ← Database access layer (SQL queries)
│   │   ├── auth.py
│   │   ├── books.py
│   │   ├── shloks.py
│   │   └── permissions.py
│   ├── services/               ← Business logic layer
│   │   ├── auth.py
│   │   ├── books.py
│   │   └── shloks.py
│   ├── api/v1/routes/          ← HTTP endpoint definitions
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── books.py
│   │   └── shloks.py
│   ├── middleware/
│   │   └── logging.py          ← Request timing and logging
│   ├── tasks/                  ← Celery background jobs
│   │   ├── celery_app.py
│   │   └── email_tasks.py
│   └── utils/                  ← Shared stateless helpers
│       ├── email.py
│       ├── pagination.py
│       ├── redis.py
│       └── supabase.py
├── tests/                      ← pytest test suite
├── alembic/                    ← Database migration scripts
├── INSTRUCTIONS.md             ← Copilot coding standards
├── SOLID.md                    ← SOLID principle compliance
├── API_README.md               ← API endpoint reference
└── requirements.txt
```

---

## How a Request Flows

```
HTTP Request
    ↓
main.py (FastAPI app)
    ↓ middleware (logging, CORS)
    ↓ exception handlers registered
    ↓
routes/auth.py (or books.py, shloks.py)
    ↓ FastAPI Depends() injects: db session, current_user
    ↓ Validates request body via Pydantic schema
    ↓
services/auth.py (business logic)
    ↓ Applies rules, checks permissions
    ↓ Raises domain exceptions if invalid
    ↓
repositories/auth.py (data access)
    ↓ Executes SQLAlchemy queries
    ↓ Returns model instances
    ↓
← Response flows back up through each layer
← Service returns schema, route wraps in ApiResponse
← Exception handler catches any ShlokVaultException → JSON error
```

---

## Key Concepts

### 1. Dependency Injection via `Depends()`

FastAPI's `Depends()` system injects:
- **`get_db`** → Yields an `AsyncSession`, auto-commits on success, auto-rollbacks on error
- **`get_current_user`** → Extracts Bearer token, decodes JWT, loads user from DB
- **`get_optional_user`** → Same as above but returns `None` instead of raising

### 2. Repository Pattern

Repositories are the **only** place database queries live. This means:
- Services never import `select`, `update`, or `delete` from SQLAlchemy
- Repositories never raise business exceptions
- Repositories are easy to mock in tests

### 3. Exception Hierarchy

```
ShlokVaultException (base)
├── NotFoundException (404)
├── ForbiddenException (403)
├── ConflictException (409)
├── UnauthorizedException (401)
├── BadRequestException (400)
└── TooManyRequestsException (429)
    ├── EmailAlreadyExists (409)
    ├── InvalidCredentials (401)
    ├── BookNotFound (404)
    ├── ShlokForbidden (403)
    └── ... etc
```

The global handler in `core/handlers.py` catches `ShlokVaultException` and returns:
```json
{ "status_code": 404, "message": "Book not found", "data": null }
```

### 4. Cursor-Based Pagination

Instead of `page` + `page_size`, we use a **cursor** (base64-encoded `created_at|id`).
- First request: no cursor → get newest items
- Next page: pass `next_cursor` from response → get items older than cursor
- Advantage: consistent results even when new items are added

### 5. Visibility + Permissions

Books and shloks have a `visibility` field:
- `public` → anyone can read
- `private` → only the owner
- `specific_users` → owner + users with a `Permission` record

Permissions are cached in Redis for 5 minutes to reduce DB queries.

---

## How to Add a New Domain

Example: Adding "Meanings" support.

1. **Create model** → `app/models/meaning.py`
2. **Register in** `app/models/__init__.py`
3. **Create schemas** → `app/schemas/meanings.py`
4. **Create exceptions** → `app/exceptions/meanings.py`
5. **Add messages** → `app/constants/messages.py` → `MEANING_MESSAGES = {...}`
6. **Create repository** → `app/repositories/meanings.py`
7. **Create service** → `app/services/meanings.py`
8. **Create routes** → `app/api/v1/routes/meanings.py`
9. **Register router** in `app/main.py` → `app.include_router(meanings_router, prefix="/api/v1")`
10. **Create migration** → `alembic revision --autogenerate -m "add meanings table"`
11. **Write tests** → `tests/test_meanings.py`

---

## Running the Project

```bash
# Install deps
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=app

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```
