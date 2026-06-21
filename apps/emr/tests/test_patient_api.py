"""API tests for patient registration and RBAC enforcement."""
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.emr.models import Patient, PatientIdentifierType
from apps.users.models import Privilege, Role, User


class PatientApiTests(APITestCase):
    def setUp(self):
        PatientIdentifierType.objects.create(name="Medraxis ID", required=True)
        view_priv = Privilege.objects.create(name="View Patients")
        add_priv = Privilege.objects.create(name="Add Patients")

        self.clinician = User.objects.create_user(
            username="doc", email="doc@x.io", password="pw-strong-123")
        role = Role.objects.create(name="Clinician")
        role.privileges.set([view_priv, add_priv])
        self.clinician.roles.add(role)

        self.viewer = User.objects.create_user(
            username="view", email="v@x.io", password="pw-strong-123")
        vrole = Role.objects.create(name="Viewer")
        vrole.privileges.set([view_priv])
        self.viewer.roles.add(vrole)

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/v1/patients/")
        self.assertEqual(resp.status_code, 401)

    def test_clinician_can_register_patient_with_auto_identifier(self):
        self.client.force_authenticate(self.clinician)
        resp = self.client.post("/api/v1/patients/", {
            "gender": "F", "given_name": "Mary", "family_name": "Phiri",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(Patient.objects.count(), 1)
        # A preferred identifier is auto-assigned.
        self.assertTrue(resp.data["identifiers"][0]["identifier"].startswith("MRX-"))

    def test_viewer_without_add_privilege_cannot_register(self):
        self.client.force_authenticate(self.viewer)
        resp = self.client.post("/api/v1/patients/", {
            "gender": "M", "given_name": "Joe", "family_name": "Doe",
        }, format="json")
        self.assertEqual(resp.status_code, 403)
