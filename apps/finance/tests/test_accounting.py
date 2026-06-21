"""Tests for the financial/accounting backbone."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.emr.models import Location
from apps.finance import services
from apps.finance.ledger import party_balance, post_account_transaction
from apps.finance.models import (
    AccountTransaction,
    ExpenseCategory,
    FinancialAccount,
    PartyLedgerEntry,
)
from apps.inventory.models import (
    Product,
    ProductCategory,
    PurchaseBill,
    Supplier,
    UnitOfMeasure,
)
from apps.pos.models import Customer, Sale, SaleLine
from apps.pos.services import add_payment, complete_sale, next_invoice_number


def _account(opening="1000.00"):
    return FinancialAccount.objects.create(
        name="Main Cash", account_type=FinancialAccount.AccountType.CASH,
        opening_balance=Decimal(opening), current_balance=Decimal(opening))


def _product():
    cat = ProductCategory.objects.create(name="Meds")
    unit = UnitOfMeasure.objects.create(name="Tab")
    return Product.objects.create(name="Amox", sku="AMOX", category=cat, unit=unit,
                                  sale_price=Decimal("2.50"), cost_price=Decimal("1.00"))


class MoneyLedgerTests(TestCase):
    def test_account_balance_moves(self):
        acc = _account("100.00")
        post_account_transaction(acc, direction=AccountTransaction.Direction.IN,
                                 amount=Decimal("50"), occurred_at="2026-01-01T10:00:00Z")
        acc.refresh_from_db()
        self.assertEqual(acc.current_balance, Decimal("150.00"))
        post_account_transaction(acc, direction=AccountTransaction.Direction.OUT,
                                 amount=Decimal("70"), occurred_at="2026-01-01T11:00:00Z")
        acc.refresh_from_db()
        self.assertEqual(acc.current_balance, Decimal("80.00"))


class ExpenseTests(TestCase):
    def test_expense_debits_account(self):
        acc = _account("500.00")
        cat = ExpenseCategory.objects.create(name="Rent")
        services.record_expense(category=cat, amount=Decimal("200"), account=acc,
                                expense_date=date(2026, 1, 5))
        acc.refresh_from_db()
        self.assertEqual(acc.current_balance, Decimal("300.00"))


class SupplierLedgerTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Acme Pharma")
        self.location = Location.objects.create(name="Store")
        self.product = _product()

    def test_purchase_bill_creates_payable_and_stock(self):
        bill = services.create_purchase_bill(
            supplier=self.supplier, location=self.location,
            items=[{"product": self.product, "quantity": 100, "unit_cost": "1.00",
                    "batch_number": "B1"}],
            bill_date=date(2026, 1, 10))
        self.assertEqual(bill.grand_total, Decimal("100.00"))
        # Supplier is owed -> negative party balance (payable).
        self.assertEqual(party_balance(self.supplier), Decimal("-100.00"))
        # Stock was received.
        self.assertEqual(self.product.quantity_on_hand, Decimal("100"))

    def test_pay_supplier_reduces_payable_and_account(self):
        acc = _account("1000.00")
        bill = services.create_purchase_bill(
            supplier=self.supplier, location=self.location,
            items=[{"product": self.product, "quantity": 100, "unit_cost": "1.00"}],
            bill_date=date(2026, 1, 10))
        services.pay_supplier(supplier=self.supplier, amount=Decimal("100"), account=acc,
                              allocations=[(bill, Decimal("100"))])
        acc.refresh_from_db()
        bill.refresh_from_db()
        self.assertEqual(acc.current_balance, Decimal("900.00"))      # money out
        self.assertEqual(bill.status, PurchaseBill.Status.PAID)
        self.assertEqual(party_balance(self.supplier), Decimal("0.00"))  # settled


class CustomerLedgerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Counter")
        self.customer = Customer.objects.create(name="Walk-in Co")
        self.product = _product()

    def test_credit_sale_then_payment_settles_customer(self):
        from apps.inventory.services import receive_stock
        receive_stock(product=self.product, location=self.location, quantity=Decimal("50"),
                      batch_number="B1")
        acc = _account("0.00")
        sale = Sale.objects.create(invoice_number=next_invoice_number(),
                                   location=self.location, customer=self.customer)
        SaleLine.objects.create(sale=sale, line_type=SaleLine.LineType.PRODUCT,
                                product=self.product, quantity=Decimal("10"),
                                unit_price=Decimal("2.50"))
        sale.recalculate(); sale.save()

        complete_sale(sale)  # posts INVOICE debit -> receivable 25.00
        self.assertEqual(party_balance(self.customer), Decimal("25.00"))

        add_payment(sale, method="CASH", amount=Decimal("25.00"), account=acc)
        acc.refresh_from_db()
        self.assertEqual(acc.current_balance, Decimal("25.00"))        # money in
        self.assertEqual(party_balance(self.customer), Decimal("0.00"))  # settled
        # Ledger has both an INVOICE and a PAYMENT_IN entry.
        types = set(PartyLedgerEntry.objects.values_list("entry_type", flat=True))
        self.assertIn(PartyLedgerEntry.EntryType.INVOICE, types)
        self.assertIn(PartyLedgerEntry.EntryType.PAYMENT_IN, types)
