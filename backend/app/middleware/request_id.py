"""Request-id middleware: assigns a unique id per request and echoes it back."""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_HEADER = "X-Request-Id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get(_HEADER) or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers[_HEADER] = rid
        return response


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "") or ""
