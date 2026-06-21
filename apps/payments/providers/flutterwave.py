"""Flutterwave adapter -- cards + African mobile money (M-Pesa, MoMo), bank.

Secrets from ``settings.PAYMENTS['flutterwave']``: ``secret_key`` (FLWSECK-…)
and ``secret_hash`` (the value configured as the webhook ``verif-hash``).
"""
import json

from apps.payments.models import PaymentIntent
from apps.payments.providers.base import (
    InitiationResult,
    PaymentError,
    PaymentProvider,
    WebhookResult,
)

API_BASE = "https://api.flutterwave.com/v3"

# Map our channel to Flutterwave payment_options.
CHANNEL_OPTIONS = {
    "CARD": "card",
    "MOBILE_MONEY": "mobilemoneyghana,mpesa,mobilemoneyuganda,mobilemoneyrwanda,mobilemoneyzambia",
    "BANK": "banktransfer",
    "USSD": "ussd",
}


class FlutterwaveProvider(PaymentProvider):
    code = "flutterwave"
    STATUS_MAP = {
        "successful": PaymentIntent.Status.SUCCEEDED,
        "completed": PaymentIntent.Status.SUCCEEDED,
        "failed": PaymentIntent.Status.FAILED,
        "cancelled": PaymentIntent.Status.CANCELLED,
        "pending": PaymentIntent.Status.PROCESSING,
    }

    def initiate(self, intent) -> InitiationResult:
        import requests

        secret = self.secret("secret_key")
        if not secret:
            raise PaymentError("Flutterwave secret_key not configured.")
        payload = {
            "tx_ref": intent.reference,
            "amount": str(intent.amount),
            "currency": intent.currency,
            "redirect_url": self.gateway.config.get("redirect_url", "https://example.com/return"),
            "payment_options": CHANNEL_OPTIONS.get(intent.channel, "card"),
            "customer": {
                "email": intent.customer_email or "customer@example.com",
                "phonenumber": intent.customer_phone,
            },
            "customizations": {"title": f"Invoice {intent.reference}"},
        }
        resp = requests.post(
            f"{API_BASE}/payments", json=payload,
            headers={"Authorization": f"Bearer {secret}"}, timeout=20,
        )
        if resp.status_code >= 400:
            raise PaymentError(f"Flutterwave error: {resp.text}")
        body = resp.json()
        return InitiationResult(
            provider_reference=intent.reference,
            checkout_url=body.get("data", {}).get("link", ""),
            raw=body,
        )

    def verify(self, intent) -> str:
        import requests

        secret = self.secret("secret_key")
        # Verify by transaction id when known, else by reference.
        resp = requests.get(
            f"{API_BASE}/transactions/verify_by_reference?tx_ref={intent.reference}",
            headers={"Authorization": f"Bearer {secret}"}, timeout=20,
        )
        if resp.status_code >= 400:
            return intent.status
        data = resp.json().get("data", {})
        return self.map_status(data.get("status", ""))

    def verify_signature(self, request) -> bool:
        """Flutterwave sends the configured ``verif-hash`` header verbatim."""
        secret_hash = self.secret("secret_hash")
        received = request.META.get("HTTP_VERIF_HASH", "")
        return bool(secret_hash) and received == secret_hash

    def parse_webhook(self, request) -> WebhookResult:
        event = json.loads(request.body.decode() or "{}")
        data = event.get("data", {})
        return WebhookResult(
            event_id=str(data.get("id", "")),
            event_type=event.get("event", ""),
            reference=data.get("tx_ref", ""),
            provider_reference=str(data.get("id", "")),
            status=self.map_status(data.get("status", "")),
            amount=str(data.get("amount", "")),
            currency=data.get("currency", ""),
            raw=event,
        )
