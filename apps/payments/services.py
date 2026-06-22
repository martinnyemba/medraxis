"""Payment-gateway orchestration: create intents, settle on success, webhooks.

On success a gateway payment is settled through the existing
``pos.add_payment`` so the money lands in the same financial-account and party
ledgers as cash -- the gateway layer does not introduce a parallel money path.
"""
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.services import audit as audit_services
from apps.payments.models import PaymentIntent, WebhookEvent
from apps.payments.providers import get_provider


def _reference():
    return f"MRX-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:10]}"


@transaction.atomic
def create_intent(*, gateway, amount, currency=None, channel=None, sale=None,
                  customer_email="", customer_phone="", organization=None):
    """Create a PaymentIntent and initiate it with the provider."""
    intent = PaymentIntent.objects.create(
        reference=_reference(),
        gateway=gateway,
        sale=sale,
        amount=Decimal(str(amount)),
        currency=currency or gateway.currency,
        channel=channel or "CARD",
        customer_email=customer_email,
        customer_phone=customer_phone,
        organization=organization,
    )
    provider = get_provider(gateway)
    result = provider.initiate(intent)
    intent.provider_reference = result.provider_reference
    intent.checkout_url = result.checkout_url
    intent.raw_response = result.raw
    intent.status = PaymentIntent.Status.PROCESSING
    intent.save(update_fields=["provider_reference", "checkout_url", "raw_response", "status"])
    audit_services.record(AuditLog.Action.CREATE, instance=intent, description="payment intent created")
    return intent


@transaction.atomic
def settle_intent(intent: PaymentIntent):
    """Mark an intent succeeded and settle its Sale (idempotent)."""
    if intent.status == PaymentIntent.Status.SUCCEEDED:
        return intent

    intent.status = PaymentIntent.Status.SUCCEEDED
    fields = ["status"]

    if intent.sale_id and intent.settled_payment_id is None:
        from apps.pos.models import Payment
        from apps.pos.services import add_payment

        method_map = {
            "MOBILE_MONEY": Payment.Method.MOBILE_MONEY,
            "BANK": Payment.Method.BANK_TRANSFER,
            "CARD": Payment.Method.CARD,
        }
        payment = add_payment(
            intent.sale,
            method=method_map.get(intent.channel, Payment.Method.CARD),
            amount=intent.amount,
            reference=intent.provider_reference or intent.reference,
            account=intent.gateway.settlement_account,
        )
        intent.settled_payment = payment
        fields.append("settled_payment")

    intent.save(update_fields=fields)
    audit_services.record(AuditLog.Action.UPDATE, instance=intent, description="payment intent settled")
    return intent


@transaction.atomic
def process_webhook(gateway, request):
    """Verify, record and (idempotently) act on a provider webhook.

    Returns the :class:`WebhookEvent`. Acts only when the signature is valid,
    the event has not been processed, and the parsed status is SUCCEEDED.
    """
    provider = get_provider(gateway)
    signature_valid = provider.verify_signature(request)

    parsed = None
    if signature_valid:
        parsed = provider.parse_webhook(request)

    # Idempotency: if we've already stored this provider event, do nothing.
    if parsed and parsed.event_id:
        existing = WebhookEvent.objects.filter(
            provider=gateway.provider, provider_event_id=parsed.event_id
        ).first()
        if existing is not None:
            return existing

    intent = None
    if parsed and parsed.reference:
        intent = PaymentIntent.objects.filter(reference=parsed.reference).first()

    event = WebhookEvent.objects.create(
        gateway=gateway,
        provider=gateway.provider,
        provider_event_id=parsed.event_id if parsed else "",
        event_type=parsed.event_type if parsed else "",
        intent=intent,
        signature_valid=signature_valid,
        payload=parsed.raw if parsed else None,
    )

    if signature_valid and intent is not None:
        if parsed.status == PaymentIntent.Status.SUCCEEDED:
            settle_intent(intent)
        elif parsed.status in (PaymentIntent.Status.FAILED, PaymentIntent.Status.CANCELLED):
            intent.status = parsed.status
            intent.failure_reason = parsed.event_type
            intent.save(update_fields=["status", "failure_reason"])
        event.processed = True
        event.save(update_fields=["processed"])

    return event
