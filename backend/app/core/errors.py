"""Structured error model and FastAPI exception handlers.

Errors never leak stack traces, SQL statements, or internal secrets. Every
client-facing error carries a stable code and the request id from the current
context.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Domain error that maps to a stable code + HTTP status."""

    code: str = "INTERNAL_ERROR"
    status: int = 500

    def __init__(self, message: str, *, code: Optional[str] = None, status: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status = status
        self.details = details or {}


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status = 404


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status = 403


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status = 401


class ValidationFailure(AppError):
    code = "VALIDATION_ERROR"
    status = 422


class ConflictError(AppError):
    code = "CONFLICT"
    status = 409


# Stable transfer-domain error codes referenced by the frontend contract.
INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
BENEFICIARY_NOT_FOUND = "BENEFICIARY_NOT_FOUND"
BENEFICIARY_AMBIGUOUS = "BENEFICIARY_AMBIGUOUS"
TRANSFER_LIMIT_EXCEEDED = "TRANSFER_LIMIT_EXCEEDED"
APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
APPROVAL_ALREADY_USED = "APPROVAL_ALREADY_USED"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
TRANSFER_OUTCOME_UNKNOWN = "TRANSFER_OUTCOME_UNKNOWN"


def _error_body(code: str, message: str, request_id: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error": {"code": code, "message": message, "requestId": request_id}}
    if details:
        body["error"]["details"] = details
    return body


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        rid = getattr(request.state, "request_id", "")
        return JSONResponse(status_code=exc.status, content=_error_body(exc.code, exc.message, rid, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        rid = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "The request was invalid.", rid, {"issues": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def _fallback_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", "")
        # Never expose internals.
        return JSONResponse(status_code=500, content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", rid))
