from app.exceptions.base import NotFoundException, ForbiddenException, ConflictException
from app.constants.messages import SHLOK_MESSAGES


class ShlokNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(SHLOK_MESSAGES["NOT_FOUND"])


class ShlokForbiddenException(ForbiddenException):
    def __init__(self):
        super().__init__(SHLOK_MESSAGES["FORBIDDEN"])


class ShlokCannotMakePrivateException(ConflictException):
    def __init__(self):
        super().__init__(SHLOK_MESSAGES["CANNOT_MAKE_PRIVATE"])
