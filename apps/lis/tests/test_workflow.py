"""Tests for the LIS result entry -> verify -> release workflow."""
from django.test import TestCase
from django.utils import timezone

from apps.emr.models import (
    Concept,
    ConceptClass,
    ConceptDatatype,
    OrderType,
    Patient,
    Person,
)
from apps.lis.models import LabResult, LabSection, LabTest, TestOrder
from apps.lis.services import enter_result, release_result, verify_result


class LabWorkflowTests(TestCase):
    def setUp(self):
        klass = ConceptClass.objects.create(name="Test")
        numeric = ConceptDatatype.objects.create(name="Numeric")
        self.analyte = Concept.objects.create(
            name="Haemoglobin", concept_class=klass, datatype=numeric,
            low_normal=12, hi_normal=16, low_critical=7,
        )
        section = LabSection.objects.create(name="Haematology")
        self.lab_test = LabTest.objects.create(
            name="Hb", test_code="HB", concept=self.analyte, section=section)
        person = Person.objects.create(gender="M")
        self.patient = Patient.objects.create(person=person)
        order_type = OrderType.objects.create(name="Test Order")
        self.order = TestOrder.objects.create(
            order_number="ORD-T-1", order_type=order_type, concept=self.analyte,
            patient=self.patient, lab_test=self.lab_test, date_activated=timezone.now(),
        )

    def test_low_value_is_flagged_critical_and_releases_to_obs(self):
        result = LabResult.objects.create(
            test_order=self.order, analyte=self.analyte, value_numeric=6.0)

        enter_result(result)
        self.assertEqual(result.flag, LabResult.Flag.CRITICAL_LOW)
        self.assertEqual(result.status, LabResult.Status.ENTERED)

        verify_result(result)
        self.assertEqual(result.status, LabResult.Status.VERIFIED)

        release_result(result)
        result.refresh_from_db()
        self.assertEqual(result.status, LabResult.Status.RELEASED)
        # Releasing mirrors the value onto the patient chart as an Obs.
        self.assertIsNotNone(result.obs)
        self.assertEqual(result.obs.value_numeric, 6.0)
        self.assertEqual(result.obs.interpretation, LabResult.Flag.CRITICAL_LOW)
        # And advances the order to completed.
        self.order.refresh_from_db()
        self.assertEqual(self.order.fulfiller_status, TestOrder.FulfillerStatus.COMPLETED)
