"""Audit logging service.

Centralises writing :class:`apps.core.models.AuditLog` rows so that views,
services and signals all record actions in a consistent way.
"""
from apps.core.middleware.audit_user import get_current_request_meta, get_current_user
from apps.core.models import AuditLog


def record(action, instance=None, *, actor=None, description="", changes=None, model_name=""):
    """Write an audit log entry.

    Falls back to the thread-local request user and metadata when explicit
    values are not supplied, so callers can stay terse.
    """
    meta = get_current_request_meta()
    actor = actor or get_current_user()
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        model_name=model_name or (instance.__class__.__name__ if instance else ""),
        object_pk=str(getattr(instance, "pk", "") or ""),
        object_uuid=getattr(instance, "uuid", None),
        description=description,
        changes=changes,
        ip_address=meta.get("ip_address"),
        request_id=meta.get("request_id", ""),
    )
