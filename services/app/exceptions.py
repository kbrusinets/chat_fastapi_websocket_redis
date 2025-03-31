from typing import Callable
from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse

from services.app.logger import logger


class ChatAppError(Exception):
    def __init__(self, message: str = 'Service is unavailable', name: str = 'ChatApp'):
        self.message = message
        self.name = name
        super().__init__(self.message, self.name)


class EntityDoesNotExistError(ChatAppError):
    pass


class EntityAlreadyExistsError(ChatAppError):
    pass


class InvalidOperationError(ChatAppError):
    pass


class AuthenticationFailed(ChatAppError):
    pass


class Forbidden(ChatAppError):
    pass


class InvalidTokenError(ChatAppError):
    pass


def create_exception_handler(
    status_code: int, initial_detail: str
) -> Callable[[Request, ChatAppError], JSONResponse]:
    detail = {'message': initial_detail}  # Using a dictionary to hold the detail

    def exception_handler(_: Request, exc: ChatAppError) -> JSONResponse:
        if exc.message:
            detail['message'] = exc.message

        if exc.name:
            detail['message'] = f'{detail['message']} [{exc.name}]'

        logger.error(exc)
        return JSONResponse(
            status_code=status_code, content={'detail': detail['message']}
        )

    return exception_handler

def add_custom_exception_handlers(app: FastAPI):
    app.add_exception_handler(
        exc_class_or_status_code=EntityDoesNotExistError,
        handler=create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail='Entity does not exist'
        )
    )

    app.add_exception_handler(
        exc_class_or_status_code=EntityAlreadyExistsError,
        handler=create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail='Entity already exists'
        )
    )

    app.add_exception_handler(
        exc_class_or_status_code=InvalidOperationError,
        handler=create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            initial_detail='Invalid operation'
        )
    )

    app.add_exception_handler(
        exc_class_or_status_code=AuthenticationFailed,
        handler=create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail='Unauthorized'
        )
    )

    app.add_exception_handler(
        exc_class_or_status_code=InvalidTokenError,
        handler=create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail='Wrong token'
        )
    )

    app.add_exception_handler(
        exc_class_or_status_code=Forbidden,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail='Forbidden'
        )
    )
