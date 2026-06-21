"""Core signal handlers (authentication auditing).

Model-level audit logging is performed in service/view layers where intent is
known (create vs update vs void). Here we only capture authentication events,
which have no obvious model save hook.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.core.models import AuditLog


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.LOGIN,
        model_name="User",
        object_pk=str(user.pk),
        ip_address=_ip(request),
        request_id=getattr(request, "request_id", ""),
    )


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user is None:
        return
    AuditLog.objects.create(
        actor=user,
        action=AuditLog.Action.LOGOUT,
        model_name="User",
        object_pk=str(user.pk),
        ip_address=_ip(request),
        request_id=getattr(request, "request_id", ""),
    )


def _ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
