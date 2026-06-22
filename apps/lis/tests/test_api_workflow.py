"""API tests for the lab-order, worksheet and specimen endpoints added for the
front-end LIS workflow (order plumbing derivation, worksheet generation,
specimen type derivation and status transition actions)."""
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.emr.models import (
    Concept,
    ConceptClass,
    ConceptDatatype,
    OrderType,
    Patient,
    Person,
)
from apps.lis.models import LabResult, LabSection, LabTest, Specimen, SpecimenType
from apps.users.models import User


class LabOrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tech", password="pw12345")
        self.client.force_authenticate(self.user)

        klass = ConceptClass.objects.create(name="Test")
        numeric = ConceptDatatype.objects.create(name="Numeric")
        self.analyte = Concept.objects.create(
            name="Glucose", concept_class=klass, datatype=numeric,
            low_normal=4, hi_normal=7,
        )
        self.section = LabSection.objects.create(name="Chemistry")
        self.specimen_type = SpecimenType.objects.create(name="Serum")
        self.lab_test = LabTest.objects.create(
            name="Fasting Glucose", test_code="FBG", concept=self.analyte,
            section=self.section, specimen_type=self.specimen_type,
        )
        # The order-creation view derives the order type from this record.
        OrderType.objects.create(name="Test Order")
        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)

    def _create_order(self):
        return self.client.post(
            "/api/v1/lab/test-orders/",
            {"patient": self.patient.id, "lab_test": self.lab_test.id},
            format="json",
        )

    def test_order_creation_derives_plumbing_from_test(self):
        res = self._create_order()
        self.assertEqual(res.status_code, 201, res.data)
        # concept, order_type, order_number and date_activated are filled in.
        self.assertEqual(res.data["concept"], self.analyte.id)
        self.assertIsNotNone(res.data["order_type"])
        self.assertTrue(res.data["order_number"])
        self.assertEqual(res.data["lab_test_name"], "Fasting Glucose")

    def test_worksheet_creates_pending_result_per_analyte_idempotently(self):
        order_id = self._create_order().data["id"]
        url = f"/api/v1/lab/test-orders/{order_id}/worksheet/"

        first = self.client.post(url, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data), 1)
        self.assertEqual(first.data[0]["status"], LabResult.Status.PENDING)
        self.assertEqual(first.data[0]["analyte"], self.analyte.id)

        # Calling again does not duplicate rows.
        second = self.client.post(url, format="json")
        self.assertEqual(len(second.data), 1)
        self.assertEqual(LabResult.objects.filter(test_order_id=order_id).count(), 1)

    def test_panel_worksheet_has_a_row_per_component(self):
        a2 = Concept.objects.create(
            name="HbA1c",
            concept_class=self.analyte.concept_class,
            datatype=self.analyte.datatype,
        )
        panel = LabTest.objects.create(
            name="Diabetes Panel", test_code="DMP", concept=self.analyte,
            section=self.section, is_panel=True,
        )
        panel.analytes.set([self.analyte, a2])
        order_id = self.client.post(
            "/api/v1/lab/test-orders/",
            {"patient": self.patient.id, "lab_test": panel.id},
            format="json",
        ).data["id"]

        res = self.client.post(
            f"/api/v1/lab/test-orders/{order_id}/worksheet/", format="json"
        )
        self.assertEqual({r["analyte"] for r in res.data}, {self.analyte.id, a2.id})

    def test_specimen_creation_derives_type_and_transitions(self):
        order_id = self._create_order().data["id"]

        created = self.client.post(
            "/api/v1/lab/specimens/",
            {"patient": self.patient.id, "orders": [order_id]},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        # Type derived from the order's test; accession number auto-assigned.
        self.assertEqual(created.data["specimen_type"], self.specimen_type.id)
        self.assertTrue(created.data["accession_number"])
        self.assertEqual(created.data["status"], Specimen.Status.ORDERED)

        sid = created.data["id"]
        collected = self.client.post(f"/api/v1/lab/specimens/{sid}/collect/", format="json")
        self.assertEqual(collected.data["status"], Specimen.Status.COLLECTED)
        self.assertIsNotNone(collected.data["collected_at"])

        received = self.client.post(f"/api/v1/lab/specimens/{sid}/receive/", format="json")
        self.assertEqual(received.data["status"], Specimen.Status.RECEIVED)
        self.assertIsNotNone(received.data["received_at"])

    def test_specimen_type_reference_endpoint(self):
        res = self.client.get("/api/v1/lab/specimen-types/")
        self.assertEqual(res.status_code, 200)
        names = [s["name"] for s in res.data["results"]]
        self.assertIn("Serum", names)
