"""Tests for notification queueing, the critical-result signal and reports."""
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
from apps.inventory.services import receive_stock
from apps.lis import services as lis_services
from apps.lis.models import LabResult, LabSection, LabTest, TestOrder
from apps.notifications.models import Notification, ReportRun
from apps.notifications.reports import run_report
from apps.notifications.services import queue_notification
from apps.notifications.tasks import generate_report_task
from apps.users.models import Provider, User


class NotificationServiceTests(TestCase):
    def test_queue_is_idempotent_on_dedupe_key(self):
        user = User.objects.create_user("u", "u@x.io", "pw-strong-123")
        n1, created1 = queue_notification(
            channel="in_app", body="hi", recipient_user=user, dedupe_key="evt-1")
        n2, created2 = queue_notification(
            channel="in_app", body="hi again", recipient_user=user, dedupe_key="evt-1")
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(n1.id, n2.id)
        self.assertEqual(Notification.objects.filter(dedupe_key="evt-1").count(), 1)

    def test_in_app_notification_is_sent_eagerly(self):
        user = User.objects.create_user("u2", "u2@x.io", "pw-strong-123")
        notification, _ = queue_notification(
            channel="in_app", body="welcome", recipient_user=user)
        notification.refresh_from_db()
        # Eager Celery delivers in-app immediately.
        self.assertEqual(notification.status, Notification.Status.SENT)


class CriticalResultSignalTests(TestCase):
    def test_released_critical_result_notifies_orderer(self):
        klass = ConceptClass.objects.create(name="Test")
        numeric = ConceptDatatype.objects.create(name="Numeric")
        analyte = Concept.objects.create(
            name="Haemoglobin", concept_class=klass, datatype=numeric,
            low_normal=12, hi_normal=16, low_critical=7)
        section = LabSection.objects.create(name="Haematology")
        lab_test = LabTest.objects.create(
            name="Hb", test_code="HB", concept=analyte, section=section)
        person = Person.objects.create(gender="M")
        patient = Patient.objects.create(person=person)

        provider_user = User.objects.create_user("doc", "doc@x.io", "pw-strong-123")
        provider = Provider.objects.create(
            name="Dr Doc", identifier="DOC1", user=provider_user)
        order_type = OrderType.objects.create(name="Test Order")
        order = TestOrder.objects.create(
            order_number="ORD-T-9", order_type=order_type, concept=analyte,
            patient=patient, lab_test=lab_test, orderer=provider,
            date_activated=timezone.now())
        result = LabResult.objects.create(
            test_order=order, analyte=analyte, value_numeric=6.0)

        lis_services.enter_result(result)
        lis_services.verify_result(result)
        lis_services.release_result(result)

        note = Notification.objects.filter(recipient_user=provider_user).first()
        self.assertIsNotNone(note)
        self.assertIn("Critical", note.subject)
        self.assertEqual(note.dedupe_key, f"critical-result-{result.pk}")


class ReportTests(TestCase):
    def test_stock_valuation_report_runs_and_attaches_file(self):
        category = ProductCategory.objects.create(name="Meds")
        unit = UnitOfMeasure.objects.create(name="Tablet")
        location = Location.objects.create(name="Store")
        product = Product.objects.create(
            name="Amox", sku="AMOX", category=category, unit=unit,
            cost_price=Decimal("1.20"))
        receive_stock(product=product, location=location, quantity=100,
                      unit_cost=Decimal("1.20"), batch_number="B1")

        filename, content, count = run_report("stock_valuation", {}, None)
        self.assertTrue(filename.endswith(".csv"))
        self.assertEqual(count, 1)
        self.assertIn(b"AMOX", content)

    def test_report_run_task_completes(self):
        report_run = ReportRun.objects.create(report_type="daily_sales", parameters={})
        generate_report_task(report_run.id)
        report_run.refresh_from_db()
        self.assertEqual(report_run.status, ReportRun.Status.COMPLETE)
        self.assertTrue(report_run.output_file.name)
