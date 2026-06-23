"""API tests for the business reports: summary, day book and outstanding."""
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.emr.models import Location
from apps.finance import services
from apps.finance.models import ExpenseCategory, FinancialAccount
from apps.inventory.models import Supplier
from apps.users.models import User


class BusinessReportsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reports-user", password="pw12345")
        self.client.force_authenticate(self.user)
        self.account = FinancialAccount.objects.create(
            name="Main Cash", opening_balance=Decimal("500"), current_balance=Decimal("500"))
        self.category = ExpenseCategory.objects.create(name="Rent")
        self.supplier = Supplier.objects.create(name="Acme Pharma")
        self.location = Location.objects.create(name="Store")

    def test_summary_includes_expenses_and_net(self):
        services.record_expense(
            category=self.category, amount=Decimal("80"), account=self.account)
        res = self.client.get("/api/v1/finance/reports/summary/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Decimal(res.data["expenses"]), Decimal("80"))
        # No collections yet, so net cash is negative by the expense amount.
        self.assertEqual(Decimal(res.data["net_cash"]), Decimal("-80"))
        self.assertTrue(any(c["category"] == "Rent" for c in res.data["expenses_by_category"]))

    def test_day_book_reports_money_out(self):
        services.record_expense(
            category=self.category, amount=Decimal("30"), account=self.account)
        today = timezone.now().date().isoformat()
        res = self.client.get("/api/v1/finance/reports/day_book/", {"date": today})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Decimal(res.data["money_out"]), Decimal("30"))
        self.assertGreaterEqual(len(res.data["entries"]), 1)

    def test_outstanding_lists_supplier_payable(self):
        services.create_purchase_bill(
            supplier=self.supplier, location=self.location, items=[],
            bill_date=timezone.now().date())
        res = self.client.get("/api/v1/finance/reports/outstanding/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIn("payable_total", res.data)
        self.assertIn("receivables", res.data)
