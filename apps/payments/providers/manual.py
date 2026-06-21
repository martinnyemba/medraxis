"""Manual / test provider -- no network, for development and tests.

Lets the full lifecycle (initiate -> webhook -> settle) run without credentials.
Its webhook accepts a simple JSON body ``{reference, status, event_id}`` and a
shared-secret header for signature simulation.
"""
import json
import uuid

from apps.payments.models import PaymentIntent
from apps.payments.providers.base import (
    InitiationResult,
    PaymentProvider,
    WebhookResult,
)


class ManualProvider(PaymentProvider):
    code = "manual"
    STATUS_MAP = {
        "succeeded": PaymentIntent.Status.SUCCEEDED,
        "success": PaymentIntent.Status.SUCCEEDED,
        "failed": PaymentIntent.Status.FAILED,
        "cancelled": PaymentIntent.Status.CANCELLED,
    }

    def initiate(self, intent) -> InitiationResult:
        ref = f"manual_{uuid.uuid4().hex[:16]}"
        return InitiationResult(
            provider_reference=ref,
            checkout_url=f"/payments/manual/checkout/{intent.reference}/",
            instructions="Test gateway: simulate a webhook to complete.",
            raw={"provider_reference": ref},
        )

    def verify(self, intent) -> str:
        # Manual provider cannot self-verify; status advances only via webhook.
        return intent.status

    def verify_signature(self, request) -> bool:
        expected = self.secret("webhook_secret", "test-secret")
        return request.META.get("HTTP_X_MANUAL_SIGNATURE") == expected

    def parse_webhook(self, request) -> WebhookResult:
        body = json.loads(request.body.decode() or "{}")
        return WebhookResult(
            event_id=body.get("event_id", uuid.uuid4().hex),
            event_type=body.get("status", ""),
            reference=body.get("reference", ""),
            provider_reference=body.get("provider_reference", ""),
            status=self.map_status(body.get("status", "")),
            amount=str(body.get("amount", "")),
            currency=body.get("currency", ""),
            raw=body,
        )
