"""Tests for the void/retire base-model behaviour and its audit trail."""
from django.test import TestCase

from apps.core.models import AuditLog
from apps.emr.models import Location, Person


class VoidableTests(TestCase):
    def setUp(self):
        self.person = Person.objects.create(gender="F")

    def test_void_hides_from_default_manager(self):
        self.person.void(reason="duplicate record")
        self.assertFalse(Person.objects.filter(pk=self.person.pk).exists())
        self.assertTrue(Person.all_objects.filter(pk=self.person.pk).exists())

        self.person.refresh_from_db()
        self.assertTrue(self.person.voided)
        self.assertEqual(self.person.void_reason, "duplicate record")

    def test_void_writes_audit_log(self):
        self.person.void(reason="duplicate record")
        log = AuditLog.objects.filter(model_name="Person", object_pk=str(self.person.pk)).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, AuditLog.Action.VOID)
        self.assertEqual(log.description, "duplicate record")

    def test_unvoid_restores_and_writes_audit_log(self):
        self.person.void(reason="oops")
        self.person.unvoid()
        self.assertTrue(Person.objects.filter(pk=self.person.pk).exists())

        self.person.refresh_from_db()
        self.assertFalse(self.person.voided)
        self.assertEqual(self.person.void_reason, "")

        log = AuditLog.objects.filter(
            model_name="Person", object_pk=str(self.person.pk), action=AuditLog.Action.UPDATE
        ).first()
        self.assertIsNotNone(log)


class RetireableTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Ward 3")

    def test_retire_hides_from_default_manager(self):
        self.location.retire(reason="closed ward")
        self.assertFalse(Location.objects.filter(pk=self.location.pk).exists())
        self.assertTrue(Location.all_objects.filter(pk=self.location.pk).exists())

        self.location.refresh_from_db()
        self.assertTrue(self.location.retired)
        self.assertEqual(self.location.retire_reason, "closed ward")

    def test_retire_writes_audit_log(self):
        self.location.retire(reason="closed ward")
        log = AuditLog.objects.filter(
            model_name="Location", object_pk=str(self.location.pk)
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, AuditLog.Action.VOID)
        self.assertEqual(log.description, "closed ward")

    def test_unretire_restores_and_writes_audit_log(self):
        self.location.retire(reason="closed ward")
        self.location.unretire()
        self.assertTrue(Location.objects.filter(pk=self.location.pk).exists())

        self.location.refresh_from_db()
        self.assertFalse(self.location.retired)
        self.assertEqual(self.location.retire_reason, "")

        log = AuditLog.objects.filter(
            model_name="Location", object_pk=str(self.location.pk), action=AuditLog.Action.UPDATE
        ).first()
        self.assertIsNotNone(log)
