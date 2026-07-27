from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


@dataclass
class ApplicationError(Exception):
    """Base error for predictable application failures."""

    message: str
    error_code: str = "application_error"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __str__(self) -> str:
        return self.message


class ResourceNotFoundError(ApplicationError):
    def __init__(self, message: str = "The requested resource was not found.") -> None:
        super().__init__(
            message=message,
            error_code="resource_not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(
            message=message,
            error_code="authentication_failed",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(ApplicationError):
    def __init__(self, message: str = "You do not have permission for this action.") -> None:
        super().__init__(
            message=message,
            error_code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(ApplicationError):
    def __init__(self, message: str = "The operation conflicts with existing data.") -> None:
        super().__init__(
            message=message,
            error_code="resource_conflict",
            status_code=status.HTTP_409_CONFLICT,
        )


class FileValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="invalid_file",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "request_id": request_id,
                }
            },
        )