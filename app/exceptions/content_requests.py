"""Content request exceptions."""

from app.exceptions.base import ShlokVaultException
from app.constants.messages import CONTENT_REQUEST_MESSAGES


class ContentRequestNotFoundException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail=CONTENT_REQUEST_MESSAGES["NOT_FOUND"])


class ContentRequestForbiddenException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail=CONTENT_REQUEST_MESSAGES["FORBIDDEN"])
