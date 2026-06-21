"""Report delivery tracking (WhatsApp / SMS / email / portal).

A LIS-specific dispatch record: which report went out, on which channel, to
whom, and its delivery status. Actual sending is delegated to the async
notifications subsystem (which gains a WhatsApp channel), so retries and
provider integration are shared with the rest of the platform.
"""
from django.db import models

from apps.core.models import TimeStampedModel


class ReportDelivery(TimeStampedModel):
    """A dispatch of a test order's report to a recipient over one channel."""

    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"
        PORTAL = "portal", "Patient portal"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        READ = "READ", "Read"
        FAILED = "FAILED", "Failed"

    class Recipient(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        REFERRER = "REFERRER", "Referring doctor"
        CLIENT = "CLIENT", "B2B client"

    test_order = models.ForeignKey(
        "lis.TestOrder", on_delete=models.CASCADE, related_name="report_deliveries"
    )
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    recipient_type = models.CharField(
        max_length=20, choices=Recipient.choices, default=Recipient.PATIENT
    )
    recipient_address = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notification = models.ForeignKey(
        "notifications.Notification", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="report_deliveries",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["test_order", "channel"])]

    def __str__(self):
        return f"{self.channel} report for order {self.test_order_id} [{self.status}]"
