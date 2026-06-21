"""Delivery channels for notifications.

Email uses Django's email backend. SMS is delivered through a pluggable backend
named by the ``NOTIFICATIONS_SMS_BACKEND`` setting (dotted path to a callable
``send(to, body) -> str``); the default is a console backend safe for
development. In-app notifications need no external delivery.
"""
import logging
from importlib import import_module

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("medraxis.notifications")


def deliver_email(notification):
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@medraxis.local")
    send_mail(
        subject=notification.subject or "Medraxis notification",
        message=notification.body,
        from_email=from_email,
        recipient_list=[notification.recipient_address],
        fail_silently=False,
    )
    return "email-sent"


def _console_sms(to, body):  # pragma: no cover - dev backend
    logger.info("SMS to %s: %s", to, body)
    return "console"


def _load_sms_backend():
    path = getattr(settings, "NOTIFICATIONS_SMS_BACKEND", "")
    if not path:
        return _console_sms
    module_path, _, attr = path.rpartition(".")
    return getattr(import_module(module_path), attr)


def deliver_sms(notification):
    backend = _load_sms_backend()
    return backend(notification.recipient_address, notification.body)


def deliver_in_app(notification):
    # In-app notifications are delivered simply by existing in the DB; the
    # recipient pulls them via the API. Nothing to send externally.
    return "stored"


CHANNELS = {
    "email": deliver_email,
    "sms": deliver_sms,
    "in_app": deliver_in_app,
}


def deliver(notification):
    handler = CHANNELS.get(notification.channel)
    if handler is None:
        raise ValueError(f"Unknown notification channel: {notification.channel}")
    return handler(notification)
