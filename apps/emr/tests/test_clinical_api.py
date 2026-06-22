"""API tests for the patient-safety clinical records: allergies, conditions, diagnoses."""
from rest_framework.test import APITestCase

from apps.emr.models import (
    Concept,
    ConceptClass,
    ConceptDatatype,
    Patient,
    PatientIdentifierType,
    Person,
)
from apps.users.models import User


class ClinicalRecordsApiTests(APITestCase):
    def setUp(self):
        PatientIdentifierType.objects.create(name="Medraxis ID", required=True)
        self.user = User.objects.create_user(
            username="doc", email="doc@x.io", password="pw-strong-123")

        cc = ConceptClass.objects.create(name="Diagnosis")
        dt = ConceptDatatype.objects.create(name="Coded")
        self.penicillin = Concept.objects.create(name="Penicillin", concept_class=cc, datatype=dt)
        self.malaria = Concept.objects.create(name="Malaria", concept_class=cc, datatype=dt)

        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)

        self.client.force_authenticate(self.user)

    def test_record_and_list_allergy(self):
        resp = self.client.post("/api/v1/allergies/", {
            "patient": self.patient.id, "allergen": self.penicillin.id,
            "category": "DRUG", "severity": "SEVERE", "reaction": "Anaphylaxis",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["allergen_name"], "Penicillin")

        listed = self.client.get(f"/api/v1/allergies/?patient={self.patient.id}")
        self.assertEqual(listed.data["count"], 1)

    def test_record_condition(self):
        resp = self.client.post("/api/v1/conditions/", {
            "patient": self.patient.id, "concept": self.malaria.id,
            "clinical_status": "ACTIVE",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["concept_name"], "Malaria")

    def test_record_diagnosis(self):
        resp = self.client.post("/api/v1/diagnoses/", {
            "patient": self.patient.id, "diagnosis_concept": self.malaria.id,
            "certainty": "CONFIRMED", "rank": 1,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["diagnosis_concept_name"], "Malaria")

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(None)
        resp = self.client.get("/api/v1/allergies/")
        self.assertEqual(resp.status_code, 401)
