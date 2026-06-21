"""Attach a correlation/request ID to every request for tracing and audit."""
import uuid


class RequestIDMiddleware:
    """Generate (or propagate) an ``X-Request-ID`` for each request.

    The id is stored on ``request.request_id`` so logging and audit records can
    correlate work belonging to a single HTTP request. No business logic lives
    here — purely a cross-cutting concern.
    """

    header = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header) or uuid.uuid4().hex
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
