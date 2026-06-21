"""Expose the current request user to the ORM layer via thread-locals.

This lets model ``save()`` overrides and signal handlers stamp ``creator`` /
``changed_by`` and write audit logs without threading the user through every
function call. Read-only access is provided through :func:`get_current_user`
and :func:`get_current_request_meta`.
"""
import threading

_state = threading.local()


def get_current_user():
    return getattr(_state, "user", None)


def get_current_request_meta():
    return {
        "ip_address": getattr(_state, "ip_address", None),
        "request_id": getattr(_state, "request_id", ""),
    }


class CurrentUserMiddleware:
    """Store the authenticated user and request metadata in thread-locals."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.user = getattr(request, "user", None)
        _state.ip_address = self._client_ip(request)
        _state.request_id = getattr(request, "request_id", "")
        try:
            return self.get_response(request)
        finally:
            # Avoid leaking state across pooled worker threads.
            _state.user = None
            _state.ip_address = None
            _state.request_id = ""

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
