"""Health check route."""

from fastapi import APIRouter
from app.constants.messages import GENERAL_MESSAGES

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": GENERAL_MESSAGES["HEALTH_OK"],
        "service": "ShlokVault API",
        "version": "1.0.0",
    }
