"""API tests for the POS sale endpoint behaviour relied on by the front-end:
location derivation, catalogue pricing on create, and the complete/pay actions."""
from decimal import Decimal

from rest_framework.test import APITestCase

from apps.emr.models import Location
from apps.inventory.models import Product, ProductCategory, UnitOfMeasure
from apps.inventory.services import receive_stock
from apps.pos.models import Sale
from apps.users.models import User


class SaleApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="pw12345")
        self.client.force_authenticate(self.user)

        self.location = Location.objects.create(name="Counter")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        self.product = Product.objects.create(
            name="Amoxicillin", sku="AMOX", category=category, unit=unit,
            sale_price=Decimal("2.50"))
        receive_stock(product=self.product, location=self.location, quantity=100,
                      batch_number="B1")

    def _create_sale(self, **extra):
        body = {
            "lines": [
                {"line_type": "PRODUCT", "product": self.product.id,
                 "description": self.product.name, "quantity": "2"}
            ],
            **extra,
        }
        return self.client.post("/api/v1/pos/sales/", body, format="json")

    def test_sale_create_derives_location_and_prices_lines(self):
        res = self._create_sale()
        self.assertEqual(res.status_code, 201, res.data)
        # Location defaulted to the only facility location.
        self.assertEqual(res.data["location"], self.location.id)
        # Unit price resolved from the product catalogue (2 x 2.50).
        self.assertEqual(Decimal(res.data["subtotal"]), Decimal("5.00"))
        self.assertEqual(res.data["status"], Sale.Status.DRAFT)

    def test_complete_then_pay_full_workflow(self):
        sale_id = self._create_sale(location=self.location.id).data["id"]

        completed = self.client.post(f"/api/v1/pos/sales/{sale_id}/complete/", format="json")
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data["status"], Sale.Status.COMPLETED)
        # Stock drawn down (100 - 2).
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_on_hand, Decimal("98"))

        balance = completed.data["balance_due"]
        paid = self.client.post(
            f"/api/v1/pos/sales/{sale_id}/pay/",
            {"method": "CASH", "amount": balance},
            format="json",
        )
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data["status"], Sale.Status.PAID)
        self.assertEqual(Decimal(paid.data["balance_due"]), Decimal("0.00"))

    def test_complete_without_stock_returns_400(self):
        empty_location = Location.objects.create(name="No-stock room")
        sale_id = self._create_sale(location=empty_location.id).data["id"]
        res = self.client.post(f"/api/v1/pos/sales/{sale_id}/complete/", format="json")
        self.assertEqual(res.status_code, 400)


class SalesReturnApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier2", password="pw12345")
        self.client.force_authenticate(self.user)

        self.location = Location.objects.create(name="Counter")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        self.product = Product.objects.create(
            name="Amoxicillin", sku="AMOX2", category=category, unit=unit,
            sale_price=Decimal("2.50"))
        receive_stock(product=self.product, location=self.location, quantity=100,
                      batch_number="B1")

        sale_res = self.client.post("/api/v1/pos/sales/", {
            "location": self.location.id,
            "lines": [
                {"line_type": "PRODUCT", "product": self.product.id,
                 "description": self.product.name, "quantity": "2"}
            ],
        }, format="json")
        self.sale_id = sale_res.data["id"]
        self.invoice_number = sale_res.data["invoice_number"]
        self.client.post(f"/api/v1/pos/sales/{self.sale_id}/complete/", format="json")
        self.product.refresh_from_db()

    def test_create_and_process_sales_return_restocks(self):
        before = self.product.quantity_on_hand

        res = self.client.post("/api/v1/pos/sales-returns/", {
            "sale": self.sale_id, "location": self.location.id,
            "return_date": "2024-01-01", "reason": "Damaged packaging",
            "lines": [
                {"product": self.product.id, "description": self.product.name,
                 "quantity": "1", "unit_price": "2.50"}
            ],
        }, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["sale_invoice_number"], self.invoice_number)
        self.assertEqual(res.data["status"], "DRAFT")

        return_id = res.data["id"]
        processed = self.client.post(f"/api/v1/pos/sales-returns/{return_id}/process/", format="json")
        self.assertEqual(processed.status_code, 200, processed.data)
        self.assertEqual(processed.data["status"], "COMPLETED")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_on_hand, before + Decimal("1"))
