"""Celery tasks for notification delivery and report generation.

With ``CELERY_TASK_ALWAYS_EAGER`` (the default when no broker is configured)
these run inline, so the system works end-to-end in development and tests
without a worker.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("medraxis.notifications")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, notification_id):
    """Deliver a single notification, retrying transient failures."""
    from apps.notifications.channels import deliver
    from apps.notifications.models import Notification

    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.warning("Notification %s vanished before delivery", notification_id)
        return "missing"

    if notification.status == Notification.Status.SENT:
        return "already-sent"

    notification.attempts += 1
    try:
        deliver(notification)
    except Exception as exc:  # noqa: BLE001 - record and retry
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)[:255]
        notification.save(update_fields=["status", "error", "attempts"])
        logger.exception("Notification %s delivery failed", notification_id)
        raise self.retry(exc=exc)

    notification.status = Notification.Status.SENT
    notification.sent_at = timezone.now()
    notification.error = ""
    notification.save(update_fields=["status", "sent_at", "error", "attempts"])
    return "sent"


@shared_task
def process_due_notifications():
    """Periodic sweep: enqueue notifications whose scheduled time has arrived.

    Intended to be run by Celery beat as a safety net for scheduled messages.
    """
    from apps.notifications.models import Notification

    due = Notification.objects.filter(
        status__in=[Notification.Status.PENDING, Notification.Status.QUEUED],
        scheduled_for__lte=timezone.now(),
    )
    count = 0
    for notification in due:
        send_notification_task.delay(notification.id)
        count += 1
    return count


@shared_task(bind=True)
def generate_report_task(self, report_run_id):
    """Run a report generator and attach its output file to the ReportRun."""
    from apps.notifications.models import ReportRun
    from apps.notifications.reports import run_report

    report_run = ReportRun.objects.get(pk=report_run_id)
    report_run.status = ReportRun.Status.RUNNING
    report_run.started_at = timezone.now()
    report_run.save(update_fields=["status", "started_at"])

    try:
        filename, content, row_count = run_report(
            report_run.report_type, report_run.parameters, report_run.organization
        )
    except Exception as exc:  # noqa: BLE001
        report_run.status = ReportRun.Status.FAILED
        report_run.error = str(exc)[:255]
        report_run.finished_at = timezone.now()
        report_run.save(update_fields=["status", "error", "finished_at"])
        logger.exception("Report %s failed", report_run_id)
        raise

    from django.core.files.base import ContentFile

    report_run.output_file.save(filename, ContentFile(content), save=False)
    report_run.row_count = row_count
    report_run.status = ReportRun.Status.COMPLETE
    report_run.finished_at = timezone.now()
    report_run.save()
    return report_run.id
