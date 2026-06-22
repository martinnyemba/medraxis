"""Tests for pharmacy dispensing: FEFO stock draw-down and order fulfilment."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.models import AuditLog
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
from apps.inventory.services import InsufficientStock, receive_stock
from apps.pharmacy.models import DrugOrder
from apps.pharmacy.services import dispense


class DispenseTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Main Pharmacy")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        self.product = Product.objects.create(
            name="Amoxicillin", sku="AMOX-500", category=category, unit=unit,
            sale_price=Decimal("1.50"),
        )
        receive_stock(product=self.product, location=self.location, quantity=20, batch_number="B1")

        klass = ConceptClass.objects.create(name="Drug")
        datatype = ConceptDatatype.objects.create(name="Text")
        concept = Concept.objects.create(name="Amoxicillin", concept_class=klass, datatype=datatype)
        order_type = OrderType.objects.create(name="Drug Order")
        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)
        self.drug_order = DrugOrder.objects.create(
            order_number="RX-1", order_type=order_type, concept=concept,
            patient=self.patient, drug=self.product, date_activated=timezone.now(),
            quantity=Decimal("10"),
        )

    def test_dispense_reduces_stock(self):
        dispense(
            product=self.product, location=self.location, quantity=10,
            patient=self.patient, drug_order=self.drug_order,
        )
        self.assertEqual(self.product.quantity_on_hand, Decimal("10"))

    def test_insufficient_stock_rolls_back_cleanly(self):
        with self.assertRaises(InsufficientStock):
            dispense(
                product=self.product, location=self.location, quantity=100,
                patient=self.patient, drug_order=self.drug_order,
            )
        # No partial ledger writes; stock is unchanged.
        self.assertEqual(self.product.quantity_on_hand, Decimal("20"))
        self.assertEqual(self.drug_order.dispenses.count(), 0)

    def test_full_dispense_completes_the_order(self):
        dispense(
            product=self.product, location=self.location, quantity=10,
            patient=self.patient, drug_order=self.drug_order,
        )
        self.drug_order.refresh_from_db()
        self.assertEqual(self.drug_order.fulfiller_status, DrugOrder.FulfillerStatus.COMPLETED)

    def test_partial_dispense_leaves_order_pending(self):
        dispense(
            product=self.product, location=self.location, quantity=4,
            patient=self.patient, drug_order=self.drug_order,
        )
        self.drug_order.refresh_from_db()
        self.assertNotEqual(self.drug_order.fulfiller_status, DrugOrder.FulfillerStatus.COMPLETED)

    def test_dispense_writes_audit_log(self):
        dispense_event = dispense(
            product=self.product, location=self.location, quantity=10,
            patient=self.patient, drug_order=self.drug_order,
        )
        log = AuditLog.objects.filter(
            model_name="Dispense", object_pk=str(dispense_event.pk)
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, AuditLog.Action.CREATE)
