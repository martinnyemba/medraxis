"""Tests for the POS -> clinical bridge on sale completion:

* a medicine (drug product) sold at the till gets a clinical Dispense record
  (controlled-drug traceability) without double-moving stock; and
* a LAB_TEST / LAB_PROFILE line opens the lab workflow (TestOrder + specimen).
"""
from decimal import Decimal

from django.test import TestCase

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
from apps.lis.models import LabSection, LabTest, SpecimenType, TestOrder
from apps.pharmacy.models import Dispense
from apps.pharmacy.services import DispenseReversalError, reverse_dispense
from apps.pos.models import Sale, SaleLine
from apps.pos.services import SaleFulfillmentError, complete_sale, next_invoice_number


class SaleFulfillmentTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Counter")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        klass = ConceptClass.objects.create(name="Drug")
        datatype = ConceptDatatype.objects.create(name="Text")

        drug_concept = Concept.objects.create(
            name="Paracetamol", concept_class=klass, datatype=datatype)
        self.drug = Product.objects.create(
            name="Paracetamol 500mg", sku="PARA-500", category=category, unit=unit,
            sale_price=Decimal("1.00"), cost_price=Decimal("0.40"),
            is_drug=True, drug_concept=drug_concept)
        receive_stock(product=self.drug, location=self.location, quantity=100,
                      batch_number="B1", unit_cost=Decimal("0.40"))

        # A lab test for the lab-bridge cases.
        section = LabSection.objects.create(name="Chemistry")
        stype = SpecimenType.objects.create(name="Serum")
        test_concept = Concept.objects.create(
            name="Glucose", concept_class=klass, datatype=datatype)
        self.lab_test = LabTest.objects.create(
            concept=test_concept, test_code="GLU", section=section,
            specimen_type=stype, price=Decimal("5.00"))
        OrderType.objects.create(name="Test Order")

        person = Person.objects.create(gender="M")
        self.patient = Patient.objects.create(person=person)

    def _sale(self, patient=None):
        return Sale.objects.create(
            invoice_number=next_invoice_number(), location=self.location, patient=patient)

    # --- Gap B: OTC medicine -> dispense record ---------------------------
    def test_drug_sale_records_dispense_without_double_moving_stock(self):
        sale = self._sale()
        SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.PRODUCT, product=self.drug,
            quantity=Decimal("10"), unit_price=Decimal("1.00"))
        complete_sale(sale)

        # Stock drawn exactly once (the SALE line), so COGS stays correct.
        self.assertEqual(self.drug.quantity_on_hand, Decimal("90"))
        dispenses = Dispense.objects.filter(sale=sale)
        self.assertEqual(dispenses.count(), 1)
        self.assertEqual(dispenses.first().batch_lines.count(), 1)

    def test_pos_dispense_cannot_be_reversed_directly(self):
        sale = self._sale()
        SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.PRODUCT, product=self.drug,
            quantity=Decimal("2"), unit_price=Decimal("1.00"))
        complete_sale(sale)
        event = Dispense.objects.get(sale=sale)
        with self.assertRaises(DispenseReversalError):
            reverse_dispense(event)

    # --- Gap A: lab test sold at POS -> lab workflow ----------------------
    def test_lab_line_opens_test_order_and_specimen(self):
        sale = self._sale(patient=self.patient)
        line = SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.LAB_TEST, lab_test=self.lab_test,
            quantity=Decimal("1"), unit_price=Decimal("5.00"))
        complete_sale(sale)

        orders = TestOrder.objects.filter(patient=self.patient, lab_test=self.lab_test)
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first().specimens.count(), 1)
        line.refresh_from_db()
        self.assertTrue(line.fulfilled)

    def test_lab_fulfilment_is_idempotent(self):
        sale = self._sale(patient=self.patient)
        SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.LAB_TEST, lab_test=self.lab_test,
            quantity=Decimal("1"), unit_price=Decimal("5.00"))
        complete_sale(sale)
        complete_sale(sale)  # re-completing must not duplicate the order
        self.assertEqual(
            TestOrder.objects.filter(patient=self.patient, lab_test=self.lab_test).count(), 1)

    def test_lab_line_without_patient_is_rejected(self):
        sale = self._sale()  # no patient
        SaleLine.objects.create(
            sale=sale, line_type=SaleLine.LineType.LAB_TEST, lab_test=self.lab_test,
            quantity=Decimal("1"), unit_price=Decimal("5.00"))
        with self.assertRaises(SaleFulfillmentError):
            complete_sale(sale)
