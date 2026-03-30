# INSTRUCTIONS.md
> **This file must be read in full before making any changes to the codebase.**
> The copilot must follow every rule here without exception.

---

## Objective

This is a brand-new backend built by deeply studying the existing **`shloks-backend`** folder and rebuilding it from scratch — cleaner, more scalable, and fully SOLID-compliant.

---

## Architecture

```
shlok-backend-recreated/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes/          # One file per feature/domain
│   ├── core/
│   │   ├── config.py            # All settings loaded from .env via Pydantic BaseSettings
│   │   ├── database.py          # Async SQLAlchemy + Supabase PostgreSQL
│   │   └── security.py          # Auth/JWT helpers
│   ├── constants/               # ALL hardcoded strings, enums, status codes, messages
│   ├── models/                  # Database models (SQLAlchemy)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Business logic — one service class per domain
│   ├── repositories/            # All database queries — one repository per model
│   ├── tasks/                   # All Celery tasks
│   ├── workers/
│   │   └── celery_app.py        # Celery app initialization
│   ├── middleware/              # Custom middleware (logging, error handling, etc.)
│   ├── exceptions/              # Custom exception classes and handlers
│   └── main.py                  # FastAPI app entry point
├── alembic/
├── alembic.ini
├── tests/
├── .env
├── requirements.txt
├── SOLID.md
├── API_README.md
└── TEACHING.md
```

---

## Coding Standards (Mandatory)

- **SOLID principles** enforced throughout
- **Constants folder** — every hardcoded value must live in `app/constants/`
- **Dependency Injection** — use FastAPI `Depends()` for services, DB, auth
- **Pydantic schemas** for all request/response — never expose raw DB models
- **Proper HTTP status codes** everywhere
- **Centralized error handling** — custom exception classes + global handler
- **Logging** — use Python `logging` module, never `print()`
- **Type hints** on every function signature
- No `any` equivalent — always explicit types
- No business logic in route handlers — extract to service layer
- No direct DB calls in routes — go through repository layer

---

## Ongoing Rules

- New feature: route → schema → service → repository → model
- New constant: goes into `app/constants/`, not inline
- New endpoint: add to `API_README.md` immediately
- Every endpoint must have tests — happy path, auth, validation, error cases
- `pytest -v` must pass with zero failures after every change
- Coverage must stay at or above 80%

---

*Last updated: see git history*
