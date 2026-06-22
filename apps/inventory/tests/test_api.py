"""API tests for the inventory endpoints used by the front-end: the unit-of-
measure reference list, product creation, stock receipt and purchase bills."""
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.emr.models import Location
from apps.inventory.models import Product, ProductCategory, Supplier, UnitOfMeasure
from apps.users.models import User


class InventoryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="storekeeper", password="pw12345")
        self.client.force_authenticate(self.user)
        self.category = ProductCategory.objects.create(name="Consumables")
        self.unit = UnitOfMeasure.objects.create(name="Box")
        self.location = Location.objects.create(name="Store")

    def test_units_reference_endpoint(self):
        res = self.client.get("/api/v1/inventory/units/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Box", [u["name"] for u in res.data["results"]])

    def test_create_product(self):
        res = self.client.post(
            "/api/v1/inventory/products/",
            {"name": "Gloves", "sku": "GLOVE-M", "category": self.category.id,
             "unit": self.unit.id, "sale_price": "5.00", "reorder_level": "20"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["quantity_on_hand"], 0)
        self.assertEqual(Product.objects.filter(sku="GLOVE-M").count(), 1)

    def test_receive_stock_increases_quantity_on_hand(self):
        product = Product.objects.create(
            name="Syringe", sku="SYR-5ML", category=self.category, unit=self.unit)
        res = self.client.post(
            "/api/v1/inventory/products/receive/",
            {"product": product.id, "location": self.location.id, "quantity": "200",
             "unit_cost": "0.30", "batch_number": "SYR-B1"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["transaction_type"], "RECEIPT")
        product.refresh_from_db()
        self.assertEqual(product.quantity_on_hand, Decimal("200"))

    def test_low_stock_lists_products_at_or_below_reorder(self):
        Product.objects.create(
            name="Low item", sku="LOW", category=self.category, unit=self.unit,
            reorder_level=Decimal("10"))
        res = self.client.get("/api/v1/inventory/products/low_stock/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("LOW", [p["sku"] for p in res.data["results"]])

    def test_create_purchase_bill_without_date_receives_stock(self):
        supplier = Supplier.objects.create(name="Acme Pharma")
        product = Product.objects.create(
            name="Gauze", sku="GAUZE-1", category=self.category, unit=self.unit)
        res = self.client.post(
            "/api/v1/inventory/purchase-bills/",
            {"supplier": supplier.id, "location": self.location.id,
             "items": [{"product": product.id, "quantity": "10", "unit_cost": "1.00"}]},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["bill_date"], str(timezone.now().date()))
        self.assertEqual(res.data["supplier_name"], "Acme Pharma")
        self.assertEqual(res.data["grand_total"], "10.00")
        product.refresh_from_db()
        self.assertEqual(product.quantity_on_hand, Decimal("10"))
