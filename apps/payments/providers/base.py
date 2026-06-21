"""Provider-agnostic payment interface.

Each provider adapter implements this contract; the rest of the platform only
talks to :class:`PaymentProvider`, never a specific gateway. Secrets are read
from ``settings.PAYMENTS[<provider>]`` (env-backed), never from the database.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass
class InitiationResult:
    """What a provider returns when a payment is initiated."""

    provider_reference: str
    checkout_url: str = ""
    raw: dict | None = None
    instructions: str = ""  # e.g. mobile-money prompt text


@dataclass
class WebhookResult:
    """Normalised outcome parsed from a provider webhook."""

    event_id: str
    event_type: str
    reference: str            # our PaymentIntent.reference
    provider_reference: str
    status: str               # one of PaymentIntent.Status values
    amount: str = ""
    currency: str = ""
    raw: dict | None = None


class PaymentError(Exception):
    """Raised when a provider call fails."""


class PaymentProvider:
    """Base class for gateway adapters."""

    code = "base"
    # Map a provider's status strings onto PaymentIntent.Status values.
    STATUS_MAP: dict = {}

    def __init__(self, gateway):
        self.gateway = gateway

    # -- configuration (secrets from env) ---------------------------------
    def secret(self, key, default=""):
        provider_conf = getattr(settings, "PAYMENTS", {}).get(self.code, {})
        return provider_conf.get(key, default)

    # -- interface --------------------------------------------------------
    def initiate(self, intent) -> InitiationResult:  # pragma: no cover - interface
        raise NotImplementedError

    def verify(self, intent) -> str:  # pragma: no cover - interface
        """Return the current PaymentIntent.Status by querying the provider."""
        raise NotImplementedError

    def verify_signature(self, request) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    def parse_webhook(self, request) -> WebhookResult:  # pragma: no cover - interface
        raise NotImplementedError

    # -- helpers ----------------------------------------------------------
    def map_status(self, provider_status: str) -> str:
        from apps.payments.models import PaymentIntent

        return self.STATUS_MAP.get(
            (provider_status or "").lower(), PaymentIntent.Status.PROCESSING
        )
