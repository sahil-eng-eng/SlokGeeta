from app.exceptions.base import NotFoundException, ForbiddenException, ConflictException
from app.constants.messages import BOOK_MESSAGES


class BookNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(BOOK_MESSAGES["NOT_FOUND"])


class BookForbiddenException(ForbiddenException):
    def __init__(self):
        super().__init__(BOOK_MESSAGES["FORBIDDEN"])


class BookCannotMakePrivateException(ConflictException):
    def __init__(self):
        super().__init__(BOOK_MESSAGES["CANNOT_MAKE_PRIVATE"])
