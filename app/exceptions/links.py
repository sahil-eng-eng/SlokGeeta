"""Link exceptions."""

from app.exceptions.base import ShlokVaultException
from app.constants.messages import LINK_MESSAGES


class SharedLinkNotFoundException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail=LINK_MESSAGES["NOT_FOUND"])
