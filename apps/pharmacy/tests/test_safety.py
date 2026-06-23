"""Tests for pharmacy clinical-safety patches: allergy-aware prescribing,
dispense reversal (restock) and prescription discontinuation."""
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.emr.models import (
    Allergy,
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
from apps.pharmacy.models import Dispense, DrugOrder
from apps.pharmacy.services import dispense, reverse_dispense
from apps.users.models import User


class PharmacySafetyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rx-safety", password="pw12345")
        self.client.force_authenticate(self.user)

        self.location = Location.objects.create(name="Pharmacy")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        klass = ConceptClass.objects.create(name="Drug")
        datatype = ConceptDatatype.objects.create(name="Text")
        self.concept = Concept.objects.create(
            name="Penicillin", concept_class=klass, datatype=datatype)
        self.product = Product.objects.create(
            name="Penicillin V 250mg", sku="PEN-250", category=category, unit=unit,
            sale_price=Decimal("2.00"), is_drug=True, drug_concept=self.concept)
        receive_stock(product=self.product, location=self.location, quantity=50,
                      batch_number="B1", unit_cost=Decimal("1.00"))
        OrderType.objects.create(name="Drug Order")
        person = Person.objects.create(gender="M")
        self.patient = Patient.objects.create(person=person)

    def _prescribe(self, **extra):
        body = {"patient": self.patient.id, "drug": self.product.id, "quantity": "10"}
        body.update(extra)
        return self.client.post("/api/v1/pharmacy/drug-orders/", body, format="json")

    # --- Allergy-aware prescribing ----------------------------------------
    def test_prescribe_blocked_by_allergy(self):
        Allergy.objects.create(
            patient=self.patient, allergen=self.concept, severity=Allergy.Severity.SEVERE)
        res = self._prescribe()
        self.assertEqual(res.status_code, 400, res.data)
        detail = res.data["error"]["detail"]
        self.assertIn("allergy", detail)
        self.assertEqual(detail["allergies"][0]["allergen"], "Penicillin")

    def test_prescribe_allows_allergy_override(self):
        Allergy.objects.create(patient=self.patient, allergen=self.concept)
        res = self._prescribe(override_allergy=True)
        self.assertEqual(res.status_code, 201, res.data)

    def test_allergy_check_endpoint(self):
        Allergy.objects.create(patient=self.patient, allergen=self.concept)
        res = self.client.get(
            "/api/v1/pharmacy/drug-orders/allergy_check/",
            {"patient": self.patient.id, "drug": self.product.id})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(len(res.data["allergies"]), 1)

    def test_no_allergy_allows_prescribing(self):
        res = self._prescribe()
        self.assertEqual(res.status_code, 201, res.data)

    # --- Discontinue -------------------------------------------------------
    def test_discontinue_prescription(self):
        rx = self._prescribe().data
        res = self.client.post(f"/api/v1/pharmacy/drug-orders/{rx['id']}/discontinue/",
                               {"reason": "Adverse reaction"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        order = DrugOrder.objects.get(pk=rx["id"])
        self.assertEqual(order.order_action, DrugOrder.Action.DISCONTINUE)
        self.assertIsNotNone(order.date_stopped)
        self.assertFalse(order.is_active)

    # --- Dispense reversal -------------------------------------------------
    def test_reverse_dispense_restocks(self):
        order = DrugOrder.objects.get(pk=self._prescribe().data["id"])
        event = dispense(product=self.product, location=self.location, quantity=10,
                         patient=self.patient, drug_order=order)
        self.assertEqual(self.product.quantity_on_hand, Decimal("40"))
        order.refresh_from_db()
        self.assertEqual(order.fulfiller_status, DrugOrder.FulfillerStatus.COMPLETED)

        reverse_dispense(event)
        event.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(event.status, Dispense.Status.RETURNED)
        self.assertEqual(self.product.quantity_on_hand, Decimal("50"))
        self.assertEqual(order.fulfiller_status, DrugOrder.FulfillerStatus.IN_PROGRESS)

    def test_reverse_endpoint(self):
        order = DrugOrder.objects.get(pk=self._prescribe().data["id"])
        event = dispense(product=self.product, location=self.location, quantity=5,
                         patient=self.patient, drug_order=order)
        res = self.client.post(f"/api/v1/pharmacy/dispenses/{event.id}/reverse/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["status"], Dispense.Status.RETURNED)
