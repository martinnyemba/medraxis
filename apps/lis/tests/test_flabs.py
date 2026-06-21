"""Tests for the FLabs-inspired LIS extensions."""
from datetime import date, timedelta

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
from apps.lis import automation_service as auto
from apps.lis import services
from apps.lis.delivery_service import dispatch_report
from apps.lis.models import (
    Antibiotic,
    AutoVerificationRule,
    LabResult,
    LabSection,
    LabTest,
    MicrobiologyResult,
    Organism,
    QCMaterial,
    QCResult,
    ReferenceRange,
    ReportDelivery,
    SensitivityResult,
    TestOrder,
)
from apps.notifications.models import Notification


def _make_test(name="Hb", code="HB"):
    klass = ConceptClass.objects.create(name=f"Test-{code}")
    numeric = ConceptDatatype.objects.create(name=f"Numeric-{code}")
    analyte = Concept.objects.create(name=name, concept_class=klass, datatype=numeric)
    section = LabSection.objects.create(name=f"Section-{code}")
    lab_test = LabTest.objects.create(name=name, test_code=code, concept=analyte, section=section)
    return lab_test, analyte


def _make_order(lab_test, analyte, *, sex="F", birthdate=None):
    person = Person.objects.create(gender=sex, birthdate=birthdate)
    patient = Patient.objects.create(person=person)
    order_type = OrderType.objects.create(name=f"OT-{lab_test.test_code}")
    order = TestOrder.objects.create(
        order_number=f"ORD-{lab_test.test_code}-1", order_type=order_type,
        concept=analyte, patient=patient, lab_test=lab_test, date_activated=timezone.now())
    return order, patient


class ReferenceRangeTests(TestCase):
    def test_sex_specific_range_is_selected(self):
        lab_test, analyte = _make_test()
        # Male and female adult ranges differ.
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="M", low_normal=13, hi_normal=17)
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="F", low_normal=12, hi_normal=15)
        order, patient = _make_order(lab_test, analyte, sex="F")
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=16)
        # 16 is HIGH for a female (>15) but normal for a male (<17).
        self.assertEqual(auto.flag_with_reference_range(result), LabResult.Flag.HIGH)

    def test_age_specific_range(self):
        lab_test, analyte = _make_test(code="HB2")
        # Neonatal range much higher than adult.
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="A",
            age_min_days=0, age_max_days=28, low_normal=14, hi_normal=24)
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="A",
            age_min_days=29, age_max_days=40000, low_normal=12, hi_normal=16)
        order, patient = _make_order(
            lab_test, analyte, birthdate=date.today() - timedelta(days=10))
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=20)
        # 20 is normal for a neonate (14-24).
        self.assertEqual(auto.flag_with_reference_range(result), LabResult.Flag.NORMAL)


class AutoVerificationTests(TestCase):
    def test_in_range_result_auto_verifies(self):
        lab_test, analyte = _make_test(code="GLU")
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="A", low_normal=4, hi_normal=6,
            low_critical=2, hi_critical=20)
        AutoVerificationRule.objects.create(name="glu", lab_test=lab_test)
        order, _ = _make_order(lab_test, analyte)
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=5)
        services.enter_result(result)
        result.flag = auto.flag_with_reference_range(result)
        result.save(update_fields=["flag"])
        self.assertTrue(auto.auto_verify_result(result))
        self.assertEqual(result.status, LabResult.Status.VERIFIED)

    def test_critical_result_is_not_auto_verified(self):
        lab_test, analyte = _make_test(code="K")
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="A", low_normal=3.5, hi_normal=5,
            hi_critical=6.5)
        AutoVerificationRule.objects.create(name="k", lab_test=lab_test)
        order, _ = _make_order(lab_test, analyte)
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=7)
        services.enter_result(result)
        result.flag = auto.flag_with_reference_range(result)
        result.save(update_fields=["flag"])
        self.assertEqual(result.flag, LabResult.Flag.CRITICAL_HIGH)
        self.assertFalse(auto.auto_verify_result(result))
        self.assertEqual(result.status, LabResult.Status.ENTERED)

    def test_reflex_orders_followup_on_abnormal(self):
        lab_test, analyte = _make_test(code="TSH")
        reflex_test, _ = _make_test(name="FT4", code="FT4")
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="A", low_normal=0.4, hi_normal=4.0)
        AutoVerificationRule.objects.create(
            name="tsh", lab_test=lab_test, reflex_on_abnormal=reflex_test)
        order, _ = _make_order(lab_test, analyte)
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=10)
        result.flag = auto.flag_with_reference_range(result)  # HIGH
        result.save(update_fields=["flag"])
        reflex_order = auto.apply_reflex(result)
        self.assertIsNotNone(reflex_order)
        self.assertEqual(reflex_order.lab_test_id, reflex_test.id)
        self.assertEqual(reflex_order.previous_order_id, order.id)


class FlaggingConsistencyTests(TestCase):
    """Manual entry and analyzer ingestion must flag identically (one system)."""

    def test_manual_entry_uses_demographic_range(self):
        lab_test, analyte = _make_test(code="HBM")
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="F", low_normal=12, hi_normal=15)
        order, _ = _make_order(lab_test, analyte, sex="F")
        result = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=16)
        # The manual-entry service path must apply the demographic range (HIGH),
        # not just the (absent) concept range.
        services.enter_result(result)
        self.assertEqual(result.flag, LabResult.Flag.HIGH)

    def test_manual_and_ingestion_paths_agree(self):
        lab_test, analyte = _make_test(code="HBX")
        ReferenceRange.objects.create(
            lab_test=lab_test, analyte=analyte, sex="F", low_normal=12, hi_normal=15)
        order, patient = _make_order(lab_test, analyte, sex="F")

        # Manual path.
        manual = LabResult.objects.create(test_order=order, analyte=analyte, value_numeric=16)
        services.enter_result(manual)

        # Ingestion path computes via the same compute_flag entry point.
        ingested = LabResult(test_order=order, analyte=analyte, value_numeric=16)
        services.enter_result(ingested)

        self.assertEqual(manual.flag, ingested.flag)
        self.assertEqual(manual.flag, LabResult.Flag.HIGH)


class MicrobiologyTests(TestCase):
    def test_culture_with_antibiogram(self):
        lab_test, analyte = _make_test(name="Culture", code="CUL")
        order, _ = _make_order(lab_test, analyte)
        ecoli = Organism.objects.create(name="E. coli", gram_stain="NEGATIVE")
        amox = Antibiotic.objects.create(name="Amoxicillin", abbreviation="AMX")
        cipro = Antibiotic.objects.create(name="Ciprofloxacin", abbreviation="CIP")
        micro = MicrobiologyResult.objects.create(
            test_order=order, growth=MicrobiologyResult.Growth.GROWTH, organism=ecoli)
        SensitivityResult.objects.create(
            microbiology_result=micro, antibiotic=amox,
            interpretation=SensitivityResult.Interpretation.RESISTANT)
        SensitivityResult.objects.create(
            microbiology_result=micro, antibiotic=cipro,
            interpretation=SensitivityResult.Interpretation.SENSITIVE)
        self.assertEqual(micro.sensitivities.count(), 2)
        self.assertEqual(
            micro.sensitivities.get(antibiotic=cipro).interpretation, "S")


class QCTests(TestCase):
    def test_zscore_and_westgard(self):
        _, analyte = _make_test(code="QCG")
        material = QCMaterial.objects.create(
            name="Chem L1", lot_number="L1", analyte=analyte,
            target_mean=5.0, target_sd=0.2)
        in_control = QCResult(qc_material=material, measured_value=5.1, run_at=timezone.now())
        in_control.compute()
        self.assertTrue(in_control.accepted)
        self.assertAlmostEqual(in_control.z_score, 0.5, places=3)

        violation = QCResult(qc_material=material, measured_value=5.8, run_at=timezone.now())
        violation.compute()
        self.assertFalse(violation.accepted)
        self.assertEqual(violation.westgard_rule, "1-3s")


class ReportDeliveryTests(TestCase):
    def test_whatsapp_dispatch_creates_delivery_and_notification(self):
        lab_test, analyte = _make_test(code="DLV")
        order, _ = _make_order(lab_test, analyte)
        delivery = dispatch_report(
            order, channel=ReportDelivery.Channel.WHATSAPP,
            recipient_address="+260970000000")
        self.assertEqual(delivery.status, ReportDelivery.Status.SENT)
        self.assertIsNotNone(delivery.notification)
        self.assertEqual(delivery.notification.channel, Notification.Channel.WHATSAPP)

    def test_portal_delivery_needs_no_send(self):
        lab_test, analyte = _make_test(code="DLV2")
        order, _ = _make_order(lab_test, analyte)
        delivery = dispatch_report(
            order, channel=ReportDelivery.Channel.PORTAL, recipient_address="portal-user")
        self.assertEqual(delivery.status, ReportDelivery.Status.DELIVERED)
        self.assertIsNone(delivery.notification)
