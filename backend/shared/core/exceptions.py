from fastapi import Request
from fastapi.responses import JSONResponse
from shared.core.error_codes import ErrorCodes


class ApiException(Exception):
    def __init__(self, error_code: ErrorCodes, detail: str = "") -> None:
        self.detail: str = detail if detail else error_code.value["status_code"]
        self.status_code: int = int(error_code.value["code"])


class NotFoundException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.NOT_FOUND, detail)


class DuplicateException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.CONFLICT, detail)


class BadRequestException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.BAD_REQUEST, detail)


class UnauthorizedException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.UNAUTHORIZED, detail)


class ForbiddenException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.FORBIDDEN, detail)


class NotImplementedException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.NOT_IMPLEMENTED, detail)


class InternalServerErrorException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.INTERNAL_SERVER_ERROR, detail)


class ServiceUnavailableException(ApiException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(ErrorCodes.SERVICE_UNAVAILABLE, detail)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiException):
        raise exc

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def handle_api_exception(status_code: int) -> None:
    match status_code:
        case 404:
            raise NotFoundException("Events not found")
        case 401:
            raise UnauthorizedException("Unauthorized")
        case 403:
            raise ForbiddenException("Forbidden")
        case 400:
            raise BadRequestException("Bad request")
        case 409:
            raise DuplicateException("Duplicate error")
        case 501:
            raise NotImplementedException("Not implemented")
        case 503:
            raise ServiceUnavailableException("Service unavailable")
        case _:
            raise InternalServerErrorException("Internal server error")