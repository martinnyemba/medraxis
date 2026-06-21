"""Notification orchestration: create rows and enqueue async delivery."""
from django.template import Context, Template
from django.utils import timezone

from apps.notifications.models import Notification, NotificationTemplate


def render_template(template: NotificationTemplate, context: dict):
    subject = Template(template.subject_template).render(Context(context))
    body = Template(template.body_template).render(Context(context))
    return subject, body


def queue_notification(*, channel, body, subject="", recipient_user=None,
                       recipient_address="", organization=None, scheduled_for=None,
                       dedupe_key=""):
    """Create a notification and enqueue its delivery (idempotent on dedupe_key).

    Returns ``(notification, created)``. When a ``dedupe_key`` is supplied and a
    matching notification already exists, no duplicate is created or sent.
    """
    if dedupe_key:
        existing = Notification.objects.filter(dedupe_key=dedupe_key).first()
        if existing is not None:
            return existing, False

    if recipient_address == "" and recipient_user is not None:
        recipient_address = getattr(recipient_user, "email", "") or ""

    notification = Notification.objects.create(
        organization=organization,
        recipient_user=recipient_user,
        recipient_address=recipient_address,
        channel=channel,
        subject=subject,
        body=body,
        scheduled_for=scheduled_for,
        dedupe_key=dedupe_key,
        status=Notification.Status.PENDING,
    )
    _enqueue(notification)
    return notification, True


def queue_from_template(template_code, context, **kwargs):
    template = NotificationTemplate.objects.get(code=template_code)
    subject, body = render_template(template, context)
    kwargs.setdefault("channel", template.default_channel)
    return queue_notification(subject=subject, body=body, **kwargs)


def _enqueue(notification):
    """Hand the notification to Celery, or send inline if it's due now."""
    from apps.notifications.tasks import send_notification_task

    if notification.scheduled_for and notification.scheduled_for > timezone.now():
        notification.status = Notification.Status.QUEUED
        notification.save(update_fields=["status"])
        send_notification_task.apply_async(
            args=[notification.id], eta=notification.scheduled_for
        )
    else:
        notification.status = Notification.Status.QUEUED
        notification.save(update_fields=["status"])
        send_notification_task.delay(notification.id)
