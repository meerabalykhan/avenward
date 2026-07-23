"""Request correlation middleware."""

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Use a safe caller ID when valid; otherwise generate a correlation ID."""

    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
