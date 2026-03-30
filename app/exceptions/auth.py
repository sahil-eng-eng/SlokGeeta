from app.exceptions.base import ConflictException, UnauthorizedException, NotFoundException
from app.constants.messages import AUTH_MESSAGES


class EmailAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["EMAIL_ALREADY_REGISTERED"])


class UsernameAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["USERNAME_ALREADY_TAKEN"])


class InvalidCredentialsException(UnauthorizedException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["INVALID_CREDENTIALS"])


class AccountNotVerifiedException(UnauthorizedException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["ACCOUNT_NOT_VERIFIED"])


class InvalidTokenException(UnauthorizedException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["INVALID_TOKEN"])


class UserNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(AUTH_MESSAGES["USER_NOT_FOUND"])
