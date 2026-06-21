"""Consistent error envelope for the API.

Every handled error is returned as::

    {"error": {"status": <int>, "type": "<ExceptionName>", "detail": ...}}

so clients can branch on a single, predictable shape.
"""
from rest_framework.views import exception_handler


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    # Unwrap DRF's {"detail": "..."} into our envelope.
    if isinstance(detail, dict) and set(detail.keys()) == {"detail"}:
        detail = detail["detail"]

    response.data = {
        "error": {
            "status": response.status_code,
            "type": exc.__class__.__name__,
            "detail": detail,
        }
    }
    return response
