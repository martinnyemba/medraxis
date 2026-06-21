"""Tests for the inventory stock ledger and FEFO issuing."""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.emr.models import Location
from apps.inventory.models import Product, ProductCategory, StockTransaction, UnitOfMeasure
from apps.inventory.services import InsufficientStock, issue_stock, receive_stock


class StockLedgerTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Store")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        self.product = Product.objects.create(
            name="Paracetamol", sku="PARA-500", category=category, unit=unit,
            sale_price=Decimal("1.00"),
        )

    def test_receipt_increases_quantity_and_writes_ledger(self):
        receive_stock(product=self.product, location=self.location, quantity=100,
                      batch_number="B1")
        self.assertEqual(self.product.quantity_on_hand, Decimal("100"))
        self.assertEqual(
            StockTransaction.objects.filter(
                transaction_type=StockTransaction.TxnType.RECEIPT).count(), 1)

    def test_issue_uses_fefo_order(self):
        # Two batches: B2 expires sooner, so it must be consumed first.
        receive_stock(product=self.product, location=self.location, quantity=10,
                      batch_number="B1", expiry_date=date.today() + timedelta(days=200))
        receive_stock(product=self.product, location=self.location, quantity=10,
                      batch_number="B2", expiry_date=date.today() + timedelta(days=30))

        issue_stock(product=self.product, location=self.location, quantity=12,
                    transaction_type=StockTransaction.TxnType.SALE)

        b1 = self.product.batches.get(batch_number="B1")
        b2 = self.product.batches.get(batch_number="B2")
        self.assertEqual(b2.quantity_on_hand, Decimal("0"))   # consumed first
        self.assertEqual(b1.quantity_on_hand, Decimal("8"))   # remainder
        self.assertEqual(self.product.quantity_on_hand, Decimal("8"))

    def test_issue_beyond_stock_raises(self):
        receive_stock(product=self.product, location=self.location, quantity=5,
                      batch_number="B1")
        with self.assertRaises(InsufficientStock):
            issue_stock(product=self.product, location=self.location, quantity=10,
                        transaction_type=StockTransaction.TxnType.SALE)
        # Ledger must be unchanged after the failed (rolled-back) issue.
        self.assertEqual(self.product.quantity_on_hand, Decimal("5"))
