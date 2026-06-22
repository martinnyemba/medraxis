"""API tests for the prescribing/dispensing endpoints used by the front-end:
drug-order plumbing derivation and dispensing against a prescription."""
from decimal import Decimal

from rest_framework.test import APITestCase

from apps.emr.models import (
    Concept,
    ConceptClass,
    ConceptDatatype,
    Location,
    OrderType,
    Patient,
    Person,
)
from apps.inventory.models import Product, ProductCategory, UnitOfMeasure
from apps.inventory.services import receive_stock
from apps.pharmacy.models import DrugOrder
from apps.users.models import User


class PrescribingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="prescriber", password="pw12345")
        self.client.force_authenticate(self.user)

        self.location = Location.objects.create(name="Pharmacy")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        klass = ConceptClass.objects.create(name="Drug")
        datatype = ConceptDatatype.objects.create(name="Text")
        self.concept = Concept.objects.create(
            name="Amoxicillin", concept_class=klass, datatype=datatype)
        self.product = Product.objects.create(
            name="Amoxicillin 500mg", sku="AMOX-500", category=category, unit=unit,
            sale_price=Decimal("1.50"), is_drug=True, drug_concept=self.concept)
        receive_stock(product=self.product, location=self.location, quantity=50,
                      batch_number="B1")
        OrderType.objects.create(name="Drug Order")
        person = Person.objects.create(gender="M")
        self.patient = Patient.objects.create(person=person)

    def _prescribe(self):
        return self.client.post(
            "/api/v1/pharmacy/drug-orders/",
            {"patient": self.patient.id, "drug": self.product.id, "quantity": "15",
             "dose": "500", "frequency": "TDS", "route": "PO"},
            format="json",
        )

    def test_prescribe_derives_plumbing_from_drug(self):
        res = self._prescribe()
        self.assertEqual(res.status_code, 201, res.data)
        # concept derived from the product's drug concept; order metadata filled.
        self.assertEqual(res.data["concept"], self.concept.id)
        self.assertIsNotNone(res.data["order_type"])
        self.assertTrue(res.data["order_number"])
        self.assertEqual(res.data["drug_name"], "Amoxicillin 500mg")

    def test_prescribe_without_drug_concept_is_rejected(self):
        bare = Product.objects.create(
            name="Mystery", sku="MYST", category=self.product.category,
            unit=self.product.unit, is_drug=True)
        res = self.client.post(
            "/api/v1/pharmacy/drug-orders/",
            {"patient": self.patient.id, "drug": bare.id, "quantity": "1"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("drug", res.data["error"]["detail"])

    def test_dispense_against_order_derives_product_and_completes(self):
        order_id = self._prescribe().data["id"]
        res = self.client.post(
            "/api/v1/pharmacy/dispenses/",
            {"drug_order": order_id, "location": self.location.id, "quantity": "15"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        # Product/patient defaulted from the prescription.
        self.assertEqual(res.data["product_name"], "Amoxicillin 500mg")
        # Stock drawn down and the order completed.
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_on_hand, Decimal("35"))
        order = DrugOrder.objects.get(pk=order_id)
        self.assertEqual(order.fulfiller_status, DrugOrder.FulfillerStatus.COMPLETED)

    def test_dispense_more_than_stock_returns_400(self):
        order_id = self._prescribe().data["id"]
        res = self.client.post(
            "/api/v1/pharmacy/dispenses/",
            {"drug_order": order_id, "location": self.location.id, "quantity": "999"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
