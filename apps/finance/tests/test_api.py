"""API tests for the finance endpoints used by the front-end: expense and
supplier-payment date defaulting, and the party-ledger lookup."""
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.emr.models import Location
from apps.finance import services
from apps.finance.models import ExpenseCategory, FinancialAccount
from apps.inventory.models import Supplier
from apps.users.models import User


class FinanceApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="finance-user", password="pw12345")
        self.client.force_authenticate(self.user)
        self.account = FinancialAccount.objects.create(
            name="Main Cash", opening_balance=Decimal("100"), current_balance=Decimal("100"))
        self.category = ExpenseCategory.objects.create(name="Utilities")
        self.supplier = Supplier.objects.create(name="Acme Pharma")

    def test_expense_create_without_date_defaults_to_today(self):
        res = self.client.post(
            "/api/v1/finance/expenses/",
            {"category": self.category.id, "amount": "50.00", "account": self.account.id},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["expense_date"], str(timezone.now().date()))
        self.assertEqual(res.data["category_name"], "Utilities")
        self.assertEqual(res.data["account_name"], "Main Cash")
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal("50.00"))

    def test_supplier_payment_create_without_date_defaults_to_today(self):
        res = self.client.post(
            "/api/v1/finance/supplier-payments/",
            {"supplier": self.supplier.id, "amount": "10.00"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["paid_on"], str(timezone.now().date()))
        self.assertEqual(res.data["supplier_name"], "Acme Pharma")

    def test_party_ledger_rejects_unknown_party_type(self):
        res = self.client.get(
            "/api/v1/finance/party-ledger/balance/", {"party_type": "client", "party_id": 1})
        self.assertEqual(res.status_code, 400)

    def test_party_ledger_supplier_balance(self):
        services.create_purchase_bill(
            supplier=self.supplier, location=Location.objects.create(name="Store"),
            items=[], bill_date=timezone.now().date(),
        )
        res = self.client.get(
            "/api/v1/finance/party-ledger/balance/",
            {"party_type": "supplier", "party_id": self.supplier.id})
        self.assertEqual(res.status_code, 200)
        self.assertIn("balance", res.data)
