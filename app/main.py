"""ShlokVault API — FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.handlers import shlokvault_exception_handler, generic_exception_handler
from app.exceptions.base import ShlokVaultException
from app.middleware.logging import RequestLoggingMiddleware
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.books import router as books_router
from app.api.v1.routes.shloks import router as shloks_router
from app.api.v1.routes.meanings import router as meanings_router
from app.api.v1.routes.friends import router as friends_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.links import router as links_router
from app.api.v1.routes.content_requests import router as content_requests_router
from app.api.v1.routes.entity_permissions import router as entity_permissions_router
from app.api.v1.routes.discover import router as discover_router
from app.api.v1.routes.kirtan import router as kirtan_router
from app.api.v1.routes.naam_jap import router as naam_jap_router
from app.api.v1.routes.schedule import router as schedule_router
from app.api.v1.routes.group import router as group_router

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="ShlokVault API",
    description="Collaborative Sanskrit verse knowledge platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 allows everyone
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Exception handlers
app.add_exception_handler(ShlokVaultException, shlokvault_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers — all under /api/v1
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1")
app.include_router(shloks_router, prefix="/api/v1")
app.include_router(meanings_router, prefix="/api/v1")
app.include_router(friends_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(links_router, prefix="/api/v1")
app.include_router(content_requests_router, prefix="/api/v1")
app.include_router(entity_permissions_router, prefix="/api/v1")
app.include_router(discover_router, prefix="/api/v1")
app.include_router(kirtan_router, prefix="/api/v1")
app.include_router(naam_jap_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(group_router, prefix="/api/v1")
