"""Tests for tenant resolution, auto-stamping and read isolation."""
from rest_framework.test import APITestCase

from apps.emr.models import Patient, PatientIdentifierType, Person
from apps.tenancy.context import organization_context
from apps.tenancy.models import Membership, Organization
from apps.users.models import Privilege, Role, User


class TenantScopingTests(APITestCase):
    def setUp(self):
        PatientIdentifierType.objects.create(name="Medraxis ID", required=True)
        self.org_a = Organization.objects.create(name="Clinic A", slug="clinic-a")
        self.org_b = Organization.objects.create(name="Clinic B", slug="clinic-b")

        view = Privilege.objects.create(name="View Patients")
        add = Privilege.objects.create(name="Add Patients")
        role = Role.objects.create(name="Clinician")
        role.privileges.set([view, add])

        self.user_a = User.objects.create_user("a", "a@x.io", "pw-strong-123")
        self.user_a.roles.add(role)
        Membership.objects.create(user=self.user_a, organization=self.org_a, is_default=True)

        self.user_b = User.objects.create_user("b", "b@x.io", "pw-strong-123")
        self.user_b.roles.add(role)
        Membership.objects.create(user=self.user_b, organization=self.org_b, is_default=True)

    def _make_patient(self, org):
        with organization_context(org):
            person = Person.objects.create(gender="F")
            return Patient.objects.create(person=person)

    def test_save_stamps_current_organization(self):
        patient = self._make_patient(self.org_a)
        self.assertEqual(patient.organization_id, self.org_a.id)

    def test_api_create_stamps_resolved_org(self):
        self.client.force_authenticate(self.user_a)
        resp = self.client.post("/api/v1/patients/", {
            "gender": "F", "given_name": "Mary", "family_name": "Phiri"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        patient = Patient.objects.get(uuid=resp.data["uuid"])
        self.assertEqual(patient.organization_id, self.org_a.id)

    def test_user_only_sees_own_org_patients(self):
        self._make_patient(self.org_a)
        self._make_patient(self.org_b)

        self.client.force_authenticate(self.user_a)
        resp = self.client.get("/api/v1/patients/")
        self.assertEqual(resp.data["count"], 1)

        self.client.force_authenticate(self.user_b)
        resp = self.client.get("/api/v1/patients/")
        self.assertEqual(resp.data["count"], 1)

    def test_unauthorized_org_header_is_denied(self):
        """A header naming an org the user can't access fails closed (403)."""
        self._make_patient(self.org_b)
        self.client.force_authenticate(self.user_a)  # member of org_a only
        resp = self.client.get("/api/v1/patients/", HTTP_X_ORGANIZATION="clinic-b")
        self.assertEqual(resp.status_code, 403)

    def test_authorized_org_header_switches_tenant(self):
        """A user who belongs to multiple orgs can target one via the header."""
        Membership.objects.create(user=self.user_a, organization=self.org_b)
        self._make_patient(self.org_b)
        self.client.force_authenticate(self.user_a)
        resp = self.client.get("/api/v1/patients/", HTTP_X_ORGANIZATION="clinic-b")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
