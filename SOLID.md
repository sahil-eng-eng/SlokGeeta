# SOLID Principles — How This Codebase Follows Them

## S — Single Responsibility Principle

| Layer | Responsibility |
|---|---|
| `app/models/` | Define database table shapes and relationships — nothing else |
| `app/schemas/` | Define request/response validation — nothing else |
| `app/repositories/` | Execute database queries — no business logic |
| `app/services/` | Enforce business rules — no SQL, no HTTP |
| `app/api/v1/routes/` | Parse HTTP, call services, format responses — no business logic |
| `app/exceptions/` | Define typed errors per domain — no handling logic |
| `app/core/handlers.py` | Convert exceptions to HTTP responses — nothing else |
| `app/middleware/` | Cross-cutting concerns (logging) — no business logic |
| `app/tasks/` | Background job definitions — delegate to utils |
| `app/utils/` | Shared utilities (email, pagination, Redis, Supabase) — stateless helpers |

Every file does **one thing**. If you need to add a feature, you never modify more than one layer's responsibility.

---

## O — Open/Closed Principle

- **New domains** are added by creating new files in each layer (`models/`, `schemas/`, `repositories/`, `services/`, `api/v1/routes/`) and registering the router in `main.py`. No existing code is modified.
- **New exception types** extend the base hierarchy in `app/exceptions/base.py`. The global handler automatically handles them — no changes needed in handlers.
- **New constants** are added to `app/constants/messages.py` — existing messages stay untouched.

---

## L — Liskov Substitution Principle

- All domain exceptions (`EmailAlreadyExists`, `BookNotFound`, `ShlokForbidden`, etc.) extend base exceptions (`ConflictException`, `NotFoundException`, `ForbiddenException`).
- The global exception handler accepts `ShlokVaultException` — any subclass works identically.
- Any repository can be swapped for a test double because services depend on the repository interface (constructor injection via `__init__`), not on concrete implementations.

---

## I — Interface Segregation Principle

- `get_current_user` provides a fully authenticated `User` — used by protected endpoints.
- `get_optional_user` provides `Optional[User]` — used by public endpoints that optionally personalize.
- Schemas are domain-specific: `CreateBookRequest` is separate from `UpdateBookRequest`. No giant "do everything" schema.
- Each route file only imports the schemas and services it needs.

---

## D — Dependency Inversion Principle

- **Routes depend on services, not repositories.** Routes never touch the database directly.
- **Services depend on repositories, not SQLAlchemy internals.** Services call `self.repo.get_by_id()`, not `session.execute()`.
- **FastAPI `Depends()` injects** the database session and current user — components never construct their own dependencies.
- **Celery tasks depend on utility functions** (`send_email`), not on SMTP implementation details.

---

## How to Verify

1. Pick any layer. Check that it never imports from the layer above it.
2. Pick any exception. Confirm the global handler catches it without special-casing.
3. Pick any service. Confirm it never executes raw SQL or returns HTTP responses.
4. Pick any route. Confirm it never queries the database or applies business rules.
