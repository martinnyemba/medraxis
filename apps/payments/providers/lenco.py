"""Lenco adapter -- African mobile money & bank collections.

Based on Lenco's public Collections API shape. Secrets from
``settings.PAYMENTS['lenco']``: ``api_key`` and ``webhook_secret``; the API
base URL is configurable via the gateway config (``base_url``) to track API
versions.
"""
import hashlib
import hmac
import json

from apps.payments.models import PaymentIntent
from apps.payments.providers.base import (
    InitiationResult,
    PaymentError,
    PaymentProvider,
    WebhookResult,
)

DEFAULT_BASE = "https://api.lenco.co/access/v1"


class LencoProvider(PaymentProvider):
    code = "lenco"
    STATUS_MAP = {
        "successful": PaymentIntent.Status.SUCCEEDED,
        "success": PaymentIntent.Status.SUCCEEDED,
        "completed": PaymentIntent.Status.SUCCEEDED,
        "failed": PaymentIntent.Status.FAILED,
        "declined": PaymentIntent.Status.FAILED,
        "cancelled": PaymentIntent.Status.CANCELLED,
        "pending": PaymentIntent.Status.PROCESSING,
        "processing": PaymentIntent.Status.PROCESSING,
    }

    def _base(self):
        return self.gateway.config.get("base_url", DEFAULT_BASE).rstrip("/")

    def initiate(self, intent) -> InitiationResult:
        import requests

        api_key = self.secret("api_key")
        if not api_key:
            raise PaymentError("Lenco api_key not configured.")
        payload = {
            "reference": intent.reference,
            "amount": str(intent.amount),
            "currency": intent.currency,
            "channel": intent.channel.lower(),
            "phone": intent.customer_phone,
            "email": intent.customer_email,
            "redirect_url": self.gateway.config.get("redirect_url", "https://example.com/return"),
        }
        resp = requests.post(
            f"{self._base()}/collections", json=payload,
            headers={"Authorization": f"Bearer {api_key}"}, timeout=20,
        )
        if resp.status_code >= 400:
            raise PaymentError(f"Lenco error: {resp.text}")
        body = resp.json()
        data = body.get("data", body)
        return InitiationResult(
            provider_reference=str(data.get("id", "") or data.get("reference", "")),
            checkout_url=data.get("authorization_url", "") or data.get("checkout_url", ""),
            instructions=data.get("instructions", ""),
            raw=body,
        )

    def verify(self, intent) -> str:
        import requests

        api_key = self.secret("api_key")
        resp = requests.get(
            f"{self._base()}/collections/status/{intent.reference}",
            headers={"Authorization": f"Bearer {api_key}"}, timeout=20,
        )
        if resp.status_code >= 400:
            return intent.status
        data = resp.json().get("data", {})
        return self.map_status(data.get("status", ""))

    def verify_signature(self, request) -> bool:
        """Verify the HMAC-SHA256 signature header over the raw body."""
        secret = self.secret("webhook_secret")
        received = request.META.get("HTTP_X_LENCO_SIGNATURE", "")
        if not secret or not received:
            return False
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, received)

    def parse_webhook(self, request) -> WebhookResult:
        event = json.loads(request.body.decode() or "{}")
        data = event.get("data", event)
        return WebhookResult(
            event_id=str(event.get("id", "") or data.get("id", "")),
            event_type=event.get("event", "") or event.get("type", ""),
            reference=data.get("reference", ""),
            provider_reference=str(data.get("id", "")),
            status=self.map_status(data.get("status", "")),
            amount=str(data.get("amount", "")),
            currency=data.get("currency", ""),
            raw=event,
        )
