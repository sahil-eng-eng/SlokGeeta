"""Chat exceptions."""

from app.exceptions.base import ShlokVaultException
from app.constants.messages import CHAT_MESSAGES


class NotFriendsException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail=CHAT_MESSAGES["NOT_FRIENDS"])


class MessageNotFoundException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail=CHAT_MESSAGES["MESSAGE_NOT_FOUND"])


class MessageForbiddenException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail=CHAT_MESSAGES["MESSAGE_FORBIDDEN"])
