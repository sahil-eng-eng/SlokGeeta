"""Global exception handlers for FastAPI."""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions.base import ShlokVaultException
from app.core.responses import ApiResponse
from app.constants.messages import GENERAL_MESSAGES


async def shlokvault_exception_handler(
    request: Request, exc: ShlokVaultException
):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            status_code=exc.status_code,
            message=exc.message,
            data=None,
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            status_code=500,
            message=GENERAL_MESSAGES["INTERNAL_ERROR"],
            data=None,
        ).model_dump(),
    )
