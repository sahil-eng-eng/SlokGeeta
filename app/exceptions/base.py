"""Custom exception hierarchy for ShlokVault."""


class ShlokVaultException(Exception):
    """Base exception for all application errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundException(ShlokVaultException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, message)


class ForbiddenException(ShlokVaultException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(403, message)


class ConflictException(ShlokVaultException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(409, message)


class UnauthorizedException(ShlokVaultException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, message)


class BadRequestException(ShlokVaultException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(400, message)


class TooManyRequestsException(ShlokVaultException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(429, message)
