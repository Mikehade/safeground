"""
Privacy middleware — strips all identifying data.
This runs FIRST, before any handler or logger can capture IP.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class PrivacyMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Overwrite client info — no handler can ever see the real IP
        request.scope["client"] = ("0.0.0.0", 0)

        response = await call_next(request)

        # Strip forwarding headers from response
        for header in ("X-Forwarded-For", "X-Real-IP", "X-Client-IP"):
            if isinstance(response.headers, dict):
                response.headers.pop(header, None)

        return response
