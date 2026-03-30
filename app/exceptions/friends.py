"""Friend-system exceptions."""

from app.exceptions.base import ShlokVaultException
from app.constants.messages import FRIEND_MESSAGES


class FriendRequestNotFoundException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail=FRIEND_MESSAGES["REQUEST_NOT_FOUND"])


class AlreadyFriendsException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=409, detail=FRIEND_MESSAGES["ALREADY_FRIENDS"])


class FriendRequestAlreadySentException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=409, detail=FRIEND_MESSAGES["REQUEST_ALREADY_SENT"])


class CannotFriendSelfException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=400, detail=FRIEND_MESSAGES["CANNOT_FRIEND_SELF"])


class FriendRequestForbiddenException(ShlokVaultException):
    def __init__(self) -> None:
        super().__init__(status_code=403, detail="You cannot perform this action")
