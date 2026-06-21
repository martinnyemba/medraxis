"""Tests for the FHIR R4 read/search facade."""
import json

from rest_framework.test import APITestCase

from apps.emr.models import (
    Patient,
    PatientIdentifier,
    PatientIdentifierType,
    Person,
    PersonName,
)
from apps.users.models import User


class FHIRFacadeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", "u@x.io", "pw-strong-123")
        self.id_type = PatientIdentifierType.objects.create(name="Medraxis ID")
        person = Person.objects.create(gender="F", birthdate="1990-05-14")
        PersonName.objects.create(
            person=person, given_name="Jane", family_name="Banda", preferred=True)
        self.patient = Patient.objects.create(person=person)
        PatientIdentifier.objects.create(
            patient=self.patient, identifier_type=self.id_type,
            identifier="MRX-000001-7", preferred=True)

    def _json(self, resp):
        return json.loads(resp.content)

    def test_capability_statement(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/fhir/metadata")
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertEqual(body["resourceType"], "CapabilityStatement")
        self.assertEqual(body["fhirVersion"], "4.0.1")

    def test_read_patient_by_uuid(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(f"/fhir/Patient/{self.patient.uuid}")
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertEqual(body["resourceType"], "Patient")
        self.assertEqual(body["gender"], "female")
        self.assertEqual(body["name"][0]["family"], "Banda")
        self.assertEqual(body["birthDate"], "1990-05-14")

    def test_search_patient_by_identifier_returns_bundle(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/fhir/Patient?identifier=MRX-000001-7")
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertEqual(body["resourceType"], "Bundle")
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["entry"][0]["resource"]["id"], str(self.patient.uuid))

    def test_unknown_resource_type_returns_operation_outcome(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/fhir/Spaceship")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self._json(resp)["resourceType"], "OperationOutcome")

    def test_requires_authentication(self):
        resp = self.client.get(f"/fhir/Patient/{self.patient.uuid}")
        self.assertEqual(resp.status_code, 401)
