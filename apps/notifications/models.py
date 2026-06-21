"""Notifications and asynchronous report runs.

Notifications are created synchronously (cheap DB row) and *delivered*
asynchronously by Celery, so request handlers never block on email/SMS. Report
generation is likewise offloaded to a worker, with the result persisted as a
downloadable file on a :class:`ReportRun`.
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class NotificationTemplate(TimeStampedModel):
    """A reusable message template rendered with Django's template engine."""

    code = models.SlugField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    subject_template = models.CharField(max_length=255, blank=True, default="")
    body_template = models.TextField(default="")
    default_channel = models.CharField(max_length=20, default="email")

    def __str__(self):
        return self.code


class Notification(TimeStampedModel):
    """A single message to a recipient on one channel."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        IN_APP = "in_app", "In-app"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        READ = "read", "Read"

    organization = models.ForeignKey(
        "tenancy.Organization", on_delete=models.CASCADE, null=True, blank=True,
        related_name="notifications",
    )
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="notifications",
    )
    recipient_address = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Email address or phone number for external channels.",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.EMAIL)
    subject = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=255, blank=True, default="")
    # De-duplication key so the same event does not notify twice.
    dedupe_key = models.CharField(max_length=128, blank=True, default="", db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_user", "status"]),
            models.Index(fields=["status", "scheduled_for"]),
        ]

    def __str__(self):
        return f"{self.channel} to {self.recipient_address or self.recipient_user} [{self.status}]"


class ReportRun(TimeStampedModel):
    """An asynchronously generated report and its output file."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(
        "tenancy.Organization", on_delete=models.CASCADE, null=True, blank=True,
        related_name="report_runs",
    )
    report_type = models.CharField(max_length=64, db_index=True)
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="report_runs",
    )
    output_file = models.FileField(upload_to="reports/%Y/%m/", null=True, blank=True)
    row_count = models.IntegerField(null=True, blank=True)
    error = models.CharField(max_length=255, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} [{self.status}]"
