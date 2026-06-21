"""Tests for the payment-gateway layer (manual e2e + adapter logic)."""
import hashlib
import hmac
import json
import time
from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from apps.emr.models import Location
from apps.finance.ledger import party_balance
from apps.finance.models import FinancialAccount
from apps.payments import services
from apps.payments.models import PaymentGateway, PaymentIntent, WebhookEvent
from apps.payments.providers import get_provider
from apps.payments.providers.flutterwave import FlutterwaveProvider
from apps.payments.providers.stripe import StripeProvider
from apps.pos.models import Customer, Sale, SaleLine


def _account():
    return FinancialAccount.objects.create(
        name="Gateway settlement", account_type=FinancialAccount.AccountType.BANK)


def _sale(amount="100.00"):
    from apps.pos.services import complete_sale

    location = Location.objects.create(name="Counter")
    customer = Customer.objects.create(name="Payer")
    sale = Sale.objects.create(
        invoice_number=f"INV-{timezone.now():%Y%m%d}-T", location=location, customer=customer)
    SaleLine.objects.create(sale=sale, line_type=SaleLine.LineType.SERVICE,
                            description="Consult", quantity=1, unit_price=Decimal(amount))
    sale.recalculate(); sale.save()
    complete_sale(sale)  # finalise the invoice before it is paid via a gateway
    return sale


@override_settings(PAYMENTS={"manual": {"webhook_secret": "test-secret"}})
class ManualGatewayFlowTests(TestCase):
    def setUp(self):
        self.account = _account()
        self.gateway = PaymentGateway.objects.create(
            name="Test gateway", provider="manual", settlement_account=self.account)

    def test_intent_creation_returns_checkout(self):
        sale = _sale("100.00")
        intent = services.create_intent(gateway=self.gateway, amount=Decimal("100.00"),
                                        sale=sale, channel="MOBILE_MONEY")
        self.assertEqual(intent.status, PaymentIntent.Status.PROCESSING)
        self.assertTrue(intent.checkout_url)
        self.assertTrue(intent.provider_reference)

    def test_webhook_settles_sale_and_posts_money(self):
        sale = _sale("100.00")
        intent = services.create_intent(gateway=self.gateway, amount=Decimal("100.00"),
                                        sale=sale, channel="MOBILE_MONEY")
        body = json.dumps({"event_id": "evt-1", "reference": intent.reference,
                           "status": "succeeded", "provider_reference": "mm-123"})
        client = Client()
        resp = client.post(
            f"/payments/webhooks/{self.gateway.id}/", data=body,
            content_type="application/json", HTTP_X_MANUAL_SIGNATURE="test-secret")
        self.assertEqual(resp.status_code, 200)

        intent.refresh_from_db(); sale.refresh_from_db()
        self.assertEqual(intent.status, PaymentIntent.Status.SUCCEEDED)
        self.assertEqual(sale.status, Sale.Status.PAID)
        self.assertIsNotNone(intent.settled_payment)
        # Money landed in the settlement account, and the customer is settled.
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal("100.00"))
        self.assertEqual(party_balance(sale.customer), Decimal("0.00"))

    def test_invalid_signature_is_recorded_and_ignored(self):
        sale = _sale("100.00")
        intent = services.create_intent(gateway=self.gateway, amount=Decimal("100.00"),
                                        sale=sale)
        body = json.dumps({"event_id": "evt-bad", "reference": intent.reference,
                           "status": "succeeded"})
        client = Client()
        resp = client.post(
            f"/payments/webhooks/{self.gateway.id}/", data=body,
            content_type="application/json", HTTP_X_MANUAL_SIGNATURE="WRONG")
        self.assertEqual(resp.status_code, 400)
        intent.refresh_from_db()
        self.assertEqual(intent.status, PaymentIntent.Status.PROCESSING)  # untouched
        self.assertTrue(WebhookEvent.objects.filter(signature_valid=False).exists())

    def test_webhook_is_idempotent(self):
        sale = _sale("100.00")
        intent = services.create_intent(gateway=self.gateway, amount=Decimal("100.00"),
                                        sale=sale)
        body = json.dumps({"event_id": "evt-dup", "reference": intent.reference,
                           "status": "succeeded"})
        client = Client()
        for _ in range(3):
            client.post(f"/payments/webhooks/{self.gateway.id}/", data=body,
                        content_type="application/json",
                        HTTP_X_MANUAL_SIGNATURE="test-secret")
        # Only one webhook event stored; account credited only once.
        self.assertEqual(
            WebhookEvent.objects.filter(provider_event_id="evt-dup").count(), 1)
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal("100.00"))


class StripeAdapterTests(TestCase):
    @override_settings(PAYMENTS={"stripe": {"webhook_secret": "whsec_test"}})
    def test_signature_verification(self):
        gateway = PaymentGateway(name="S", provider="stripe")
        provider = StripeProvider(gateway)
        payload = json.dumps({"id": "evt", "type": "checkout.session.completed",
                              "data": {"object": {"client_reference_id": "ref1",
                                                  "payment_status": "paid", "id": "cs_1"}}})
        ts = str(int(time.time()))
        sig = hmac.new(b"whsec_test", f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()

        class Req:
            body = payload.encode()
            META = {"HTTP_STRIPE_SIGNATURE": f"t={ts},v1={sig}"}

        self.assertTrue(provider.verify_signature(Req()))
        parsed = provider.parse_webhook(Req())
        self.assertEqual(parsed.reference, "ref1")
        self.assertEqual(parsed.status, PaymentIntent.Status.SUCCEEDED)

    @override_settings(PAYMENTS={"stripe": {"webhook_secret": "whsec_test"}})
    def test_bad_signature_rejected(self):
        provider = StripeProvider(PaymentGateway(name="S", provider="stripe"))

        class Req:
            body = b"{}"
            META = {"HTTP_STRIPE_SIGNATURE": "t=1,v1=deadbeef"}

        self.assertFalse(provider.verify_signature(Req()))


class FlutterwaveAdapterTests(TestCase):
    @override_settings(PAYMENTS={"flutterwave": {"secret_hash": "myhash"}})
    def test_verif_hash_and_parse(self):
        provider = FlutterwaveProvider(PaymentGateway(name="F", provider="flutterwave"))
        payload = json.dumps({"event": "charge.completed",
                              "data": {"id": 99, "tx_ref": "ref9", "status": "successful",
                                       "amount": 100, "currency": "ZMW"}})

        class Req:
            body = payload.encode()
            META = {"HTTP_VERIF_HASH": "myhash"}

        self.assertTrue(provider.verify_signature(Req()))
        parsed = provider.parse_webhook(Req())
        self.assertEqual(parsed.reference, "ref9")
        self.assertEqual(parsed.status, PaymentIntent.Status.SUCCEEDED)
        # Wrong hash rejected.
        Req.META = {"HTTP_VERIF_HASH": "nope"}
        self.assertFalse(provider.verify_signature(Req()))


class RegistryTests(TestCase):
    def test_get_provider_by_code(self):
        for code, cls_name in [("stripe", "StripeProvider"),
                               ("flutterwave", "FlutterwaveProvider"),
                               ("lenco", "LencoProvider"), ("manual", "ManualProvider")]:
            provider = get_provider(PaymentGateway(name="x", provider=code))
            self.assertEqual(provider.__class__.__name__, cls_name)
