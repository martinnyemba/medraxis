"""Online payment gateways (Stripe, Flutterwave, Lenco) behind one interface.

A :class:`PaymentGateway` is per-tenant, non-secret configuration; provider
secrets are resolved from the environment (never stored here). A
:class:`PaymentIntent` is one payment attempt that, on success, settles a
``pos.Sale`` through the existing ``pos.add_payment`` (so gateway money lands in
the same financial-account + party ledgers as cash). :class:`WebhookEvent`
records every inbound provider callback for idempotent processing.

See ``docs/payment_gateways.md``.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel
from apps.tenancy.mixins import TenantScopedModel


class Provider(models.TextChoices):
    STRIPE = "stripe", "Stripe"
    FLUTTERWAVE = "flutterwave", "Flutterwave"
    LENCO = "lenco", "Lenco"
    MANUAL = "manual", "Manual / test"


class Channel(models.TextChoices):
    CARD = "CARD", "Card"
    MOBILE_MONEY = "MOBILE_MONEY", "Mobile money"
    BANK = "BANK", "Bank transfer"
    USSD = "USSD", "USSD"


class PaymentGateway(BaseOpenmrsMetadata, TenantScopedModel):
    """A configured payment provider for a tenant (no secrets stored)."""

    provider = models.CharField(max_length=20, choices=Provider.choices)
    is_active = models.BooleanField(default=True)
    is_test = models.BooleanField(default=True)
    currency = models.CharField(max_length=8, default="USD")
    supported_channels = models.JSONField(
        default=list, blank=True,
        help_text="List of channels, e.g. ['CARD', 'MOBILE_MONEY'].",
    )
    # Where settled money is recorded (money-in lands in this account).
    settlement_account = models.ForeignKey(
        "finance.FinancialAccount", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="gateways",
    )
    # Optional non-secret public/config values (publishable key, base URL, ...).
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"


class PaymentIntent(TimeStampedModel, TenantScopedModel):
    """A single payment attempt against a gateway, linked to a Sale."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    reference = models.CharField(max_length=80, unique=True, db_index=True)
    gateway = models.ForeignKey(
        PaymentGateway, on_delete=models.PROTECT, related_name="intents"
    )
    sale = models.ForeignKey(
        "pos.Sale", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_intents"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.CARD)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    customer_email = models.EmailField(blank=True, default="")
    customer_phone = models.CharField(max_length=32, blank=True, default="")
    # Provider's id for this transaction and the hosted checkout URL.
    provider_reference = models.CharField(max_length=120, blank=True, default="", db_index=True)
    checkout_url = models.URLField(blank=True, default="")
    settled_payment = models.ForeignKey(
        "pos.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_intent"
    )
    raw_response = models.JSONField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.reference} {self.amount} {self.currency} [{self.status}]"

    @property
    def is_settled(self):
        return self.status == self.Status.SUCCEEDED


class WebhookEvent(TimeStampedModel):
    """An inbound provider webhook, stored for idempotent processing & audit."""

    gateway = models.ForeignKey(
        PaymentGateway, on_delete=models.CASCADE, related_name="webhook_events", null=True, blank=True
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_event_id = models.CharField(max_length=160, blank=True, default="", db_index=True)
    event_type = models.CharField(max_length=80, blank=True, default="")
    intent = models.ForeignKey(
        PaymentIntent, on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_events"
    )
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["provider", "provider_event_id"])]

    def __str__(self):
        return f"{self.provider}:{self.event_type} ({'ok' if self.signature_valid else 'bad-sig'})"
