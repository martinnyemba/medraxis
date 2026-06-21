"""Lightweight structured request logging.

Logs method, path, status and duration. Intentionally avoids touching the
database or request body so it stays cheap and never logs sensitive payloads.
"""
import logging
import time

logger = logging.getLogger("medraxis.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms) request_id=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            getattr(request, "request_id", "-"),
        )
        return response
