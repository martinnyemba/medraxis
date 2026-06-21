"""Tests for POS sale totals and stock-coupled completion."""
from decimal import Decimal

from django.test import TestCase

from apps.emr.models import Location
from apps.inventory.models import Product, ProductCategory, UnitOfMeasure
from apps.inventory.services import receive_stock
from apps.pos.models import Sale, SaleLine
from apps.pos.services import add_payment, complete_sale, next_invoice_number


class SaleTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Counter")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        self.product = Product.objects.create(
            name="Amoxicillin", sku="AMOX", category=category, unit=unit,
            sale_price=Decimal("2.50"))
        receive_stock(product=self.product, location=self.location, quantity=100,
                      batch_number="B1")

    def test_totals_with_discount_and_tax(self):
        sale = Sale.objects.create(invoice_number=next_invoice_number(), location=self.location)
        SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.PRODUCT, product=self.product,
            quantity=Decimal("10"), unit_price=Decimal("2.50"),
            discount_percent=Decimal("10"), tax_percent=Decimal("5"))
        sale.recalculate()
        # gross 25.00, discount 2.50, taxable 22.50, tax 1.125->1.13, total 23.63
        self.assertEqual(sale.subtotal, Decimal("25.00"))
        self.assertEqual(sale.discount_total, Decimal("2.50"))
        self.assertEqual(sale.tax_total, Decimal("1.13"))
        self.assertEqual(sale.grand_total, Decimal("23.63"))

    def test_complete_sale_draws_down_stock_once(self):
        sale = Sale.objects.create(invoice_number=next_invoice_number(), location=self.location)
        SaleLine.objects.create(
            sale=sale, product=self.product, quantity=Decimal("10"),
            unit_price=Decimal("2.50"))
        complete_sale(sale)
        self.assertEqual(self.product.quantity_on_hand, Decimal("90"))
        # Idempotent: completing again must not deduct stock twice.
        complete_sale(sale)
        self.assertEqual(self.product.quantity_on_hand, Decimal("90"))

    def test_payment_marks_sale_paid(self):
        sale = Sale.objects.create(invoice_number=next_invoice_number(), location=self.location)
        SaleLine.objects.create(
            sale=sale, product=self.product, quantity=Decimal("2"),
            unit_price=Decimal("2.50"))
        complete_sale(sale)
        add_payment(sale, method="CASH", amount=sale.grand_total)
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.PAID)
        self.assertEqual(sale.balance_due, Decimal("0.00"))
