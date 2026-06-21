"""Smoke tests for PDF document generation (receipts, labels, reports)."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

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
from apps.lis.documents import build_lab_report_pdf, build_specimen_label_pdf
from apps.lis.models import LabResult, LabSection, LabTest, Specimen, SpecimenType, TestOrder
from apps.pos.documents import build_receipt_pdf
from apps.pos.models import Sale, SaleLine
from apps.pos.services import next_invoice_number


class PdfGenerationTests(TestCase):
    def test_receipt_pdf_is_valid(self):
        location = Location.objects.create(name="Counter")
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        product = Product.objects.create(
            name="Amox", sku="AMOX", category=category, unit=unit,
            sale_price=Decimal("2.50"))
        sale = Sale.objects.create(invoice_number=next_invoice_number(), location=location)
        SaleLine.objects.create(
            sale=sale, product=product, quantity=Decimal("2"),
            unit_price=Decimal("2.50"), tax_percent=Decimal("5"))
        sale.recalculate()
        sale.save()

        pdf = build_receipt_pdf(sale)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 800)

    def test_specimen_label_and_lab_report_pdf(self):
        klass = ConceptClass.objects.create(name="Test")
        numeric = ConceptDatatype.objects.create(name="Numeric")
        analyte = Concept.objects.create(
            name="Haemoglobin", concept_class=klass, datatype=numeric)
        section = LabSection.objects.create(name="Haematology")
        lab_test = LabTest.objects.create(
            name="Hb", test_code="HB", concept=analyte, section=section)
        blood = SpecimenType.objects.create(name="Blood")
        person = Person.objects.create(gender="F")
        patient = Patient.objects.create(person=person)
        order_type = OrderType.objects.create(name="Test Order")
        order = TestOrder.objects.create(
            order_number="ORD-T-1", order_type=order_type, concept=analyte,
            patient=patient, lab_test=lab_test, date_activated=timezone.now())
        specimen = Specimen.objects.create(
            accession_number="ACC-1", patient=patient, specimen_type=blood)
        LabResult.objects.create(
            test_order=order, analyte=analyte, value_numeric=13.5, units="g/dL")

        label = build_specimen_label_pdf(specimen)
        report = build_lab_report_pdf(order)
        self.assertTrue(label.startswith(b"%PDF"))
        self.assertTrue(report.startswith(b"%PDF"))
