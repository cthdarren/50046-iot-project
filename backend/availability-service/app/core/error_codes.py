from enum import Enum


class ErrorCodes(Enum):
    NOT_FOUND = {"code": "404", "message": "Resource not found."}
    CONFLICT = {"code": "409", "message": "Resource already exists."}
    BAD_REQUEST = {"code": "400", "message": "Request could not be processed."}
    UNAUTHORIZED = {"code": "401", "message": "Unauthorized."}
    FORBIDDEN = {"code": "403", "message": "Forbidden."}
    NOT_IMPLEMENTED = {"code": "501", "message": "Not implemented."}
    INTERNAL_SERVER_ERROR = {"code": "500", "message": "Internal server error."}
    SERVICE_UNAVAILABLE = {"code": "503", "message": "Service unavailable."}
