"""Meaning-specific exceptions."""

from app.exceptions.base import NotFoundException, ForbiddenException, ConflictException
from app.constants.messages import MEANING_MESSAGES


class MeaningNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(MEANING_MESSAGES["NOT_FOUND"])


class MeaningForbiddenException(ForbiddenException):
    def __init__(self):
        super().__init__(MEANING_MESSAGES["FORBIDDEN"])


class MeaningCannotMakePrivateException(ConflictException):
    def __init__(self):
        super().__init__(MEANING_MESSAGES["CANNOT_MAKE_PRIVATE"])
