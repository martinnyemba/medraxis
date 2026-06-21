"""Stripe adapter -- hosted Checkout Sessions + signed webhooks.

Cards/wallets (global). Secrets from ``settings.PAYMENTS['stripe']``:
``secret_key`` (sk_…) and ``webhook_secret`` (whsec_…).
"""
import hashlib
import hmac
import json
import time

from apps.payments.models import PaymentIntent
from apps.payments.providers.base import (
    InitiationResult,
    PaymentError,
    PaymentProvider,
    WebhookResult,
)

API_BASE = "https://api.stripe.com/v1"


class StripeProvider(PaymentProvider):
    code = "stripe"
    STATUS_MAP = {
        "paid": PaymentIntent.Status.SUCCEEDED,
        "complete": PaymentIntent.Status.SUCCEEDED,
        "succeeded": PaymentIntent.Status.SUCCEEDED,
        "unpaid": PaymentIntent.Status.PENDING,
        "no_payment_required": PaymentIntent.Status.SUCCEEDED,
        "canceled": PaymentIntent.Status.CANCELLED,
        "expired": PaymentIntent.Status.CANCELLED,
        "payment_failed": PaymentIntent.Status.FAILED,
    }

    def initiate(self, intent) -> InitiationResult:
        import requests

        secret = self.secret("secret_key")
        if not secret:
            raise PaymentError("Stripe secret_key not configured.")
        # Stripe amounts are in the smallest currency unit (cents).
        amount_minor = int((intent.amount * 100).to_integral_value())
        success_url = self.gateway.config.get("success_url", "https://example.com/success")
        cancel_url = self.gateway.config.get("cancel_url", "https://example.com/cancel")
        data = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": intent.reference,
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": intent.currency.lower(),
            "line_items[0][price_data][unit_amount]": amount_minor,
            "line_items[0][price_data][product_data][name]": f"Invoice {intent.reference}",
        }
        if intent.customer_email:
            data["customer_email"] = intent.customer_email
        resp = requests.post(
            f"{API_BASE}/checkout/sessions", data=data,
            auth=(secret, ""), timeout=20,
        )
        if resp.status_code >= 400:
            raise PaymentError(f"Stripe error: {resp.text}")
        body = resp.json()
        return InitiationResult(
            provider_reference=body.get("id", ""),
            checkout_url=body.get("url", ""),
            raw=body,
        )

    def verify(self, intent) -> str:
        import requests

        secret = self.secret("secret_key")
        resp = requests.get(
            f"{API_BASE}/checkout/sessions/{intent.provider_reference}",
            auth=(secret, ""), timeout=20,
        )
        if resp.status_code >= 400:
            return intent.status
        return self.map_status(resp.json().get("payment_status", ""))

    def verify_signature(self, request) -> bool:
        """Verify the ``Stripe-Signature`` header (t=…,v1=…) via HMAC-SHA256."""
        secret = self.secret("webhook_secret")
        header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        if not secret or not header:
            return False
        parts = dict(
            p.split("=", 1) for p in header.split(",") if "=" in p
        )
        timestamp, signature = parts.get("t"), parts.get("v1")
        if not timestamp or not signature:
            return False
        signed_payload = f"{timestamp}.{request.body.decode()}".encode()
        expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        # Reject very old timestamps (replay protection: 5 minutes).
        try:
            if abs(time.time() - int(timestamp)) > 300:
                return False
        except ValueError:
            return False
        return hmac.compare_digest(expected, signature)

    def parse_webhook(self, request) -> WebhookResult:
        event = json.loads(request.body.decode() or "{}")
        obj = event.get("data", {}).get("object", {})
        reference = obj.get("client_reference_id", "") or obj.get("metadata", {}).get("reference", "")
        status_field = obj.get("payment_status") or obj.get("status", "")
        return WebhookResult(
            event_id=event.get("id", ""),
            event_type=event.get("type", ""),
            reference=reference,
            provider_reference=obj.get("id", ""),
            status=self.map_status(status_field),
            amount=str(obj.get("amount_total", "")),
            currency=obj.get("currency", ""),
            raw=event,
        )
