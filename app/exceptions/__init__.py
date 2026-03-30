from app.exceptions.base import ShlokVaultException
from app.exceptions.auth import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    AccountNotVerifiedException,
    InvalidTokenException,
    UserNotFoundException,
)
from app.exceptions.books import BookNotFoundException, BookForbiddenException
from app.exceptions.shloks import ShlokNotFoundException, ShlokForbiddenException
from app.exceptions.meanings import MeaningNotFoundException, MeaningForbiddenException
from app.exceptions.friends import (
    FriendRequestNotFoundException,
    AlreadyFriendsException,
    FriendRequestAlreadySentException,
    CannotFriendSelfException,
    FriendRequestForbiddenException,
)
from app.exceptions.chat import NotFriendsException
from app.exceptions.links import SharedLinkNotFoundException
from app.exceptions.content_requests import (
    ContentRequestNotFoundException,
    ContentRequestForbiddenException,
)

__all__ = [
    "ShlokVaultException",
    "EmailAlreadyExistsException",
    "UsernameAlreadyExistsException",
    "InvalidCredentialsException",
    "AccountNotVerifiedException",
    "InvalidTokenException",
    "UserNotFoundException",
    "BookNotFoundException",
    "BookForbiddenException",
    "ShlokNotFoundException",
    "ShlokForbiddenException",
    "MeaningNotFoundException",
    "MeaningForbiddenException",
    "FriendRequestNotFoundException",
    "AlreadyFriendsException",
    "FriendRequestAlreadySentException",
    "CannotFriendSelfException",
    "FriendRequestForbiddenException",
    "NotFriendsException",
    "SharedLinkNotFoundException",
    "ContentRequestNotFoundException",
    "ContentRequestForbiddenException",
]

