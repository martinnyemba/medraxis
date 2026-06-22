"""API tests for post-registration person/patient demographics editing:
names, identifiers, addresses and custom attributes."""
from rest_framework.test import APITestCase

from apps.emr.models import (
    Patient,
    PatientIdentifierType,
    Person,
    PersonAttributeType,
)
from apps.users.models import Privilege, Role, User


class PersonDemographicsApiTests(APITestCase):
    def setUp(self):
        self.id_type = PatientIdentifierType.objects.create(name="Medraxis ID", required=True)

        self.user = User.objects.create_user("doc", "doc@x.io", "pw-strong-123")
        role = Role.objects.create(name="Clinician")
        role.privileges.set([
            Privilege.objects.create(name="View Patients"),
            Privilege.objects.create(name="Edit Patients"),
        ])
        self.user.roles.add(role)
        self.client.force_authenticate(self.user)

        self.person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=self.person)

    def test_patient_serializer_exposes_person_id(self):
        resp = self.client.get(f"/api/v1/patients/{self.patient.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["person_id"], self.person.id)

    def test_add_a_second_name(self):
        resp = self.client.post("/api/v1/person-names/", {
            "person": self.person.id, "given_name": "Alias", "family_name": "Name",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(self.person.names.count(), 1)

    def test_add_a_second_identifier(self):
        resp = self.client.post("/api/v1/patient-identifiers/", {
            "patient": self.patient.id, "identifier_type": self.id_type.id,
            "identifier": "MRX-99999",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(self.patient.identifiers.count(), 1)

    def test_add_address(self):
        resp = self.client.post("/api/v1/person-addresses/", {
            "person": self.person.id, "address1": "123 Main St",
            "city_village": "Lusaka", "country": "Zambia", "preferred": True,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["city_village"], "Lusaka")

    def test_add_custom_attribute(self):
        attr_type = PersonAttributeType.objects.create(name="Occupation", format="java.lang.String")
        resp = self.client.post("/api/v1/person-attributes/", {
            "person": self.person.id, "attribute_type": attr_type.id, "value": "Teacher",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["attribute_type_name"], "Occupation")

    def test_attribute_type_reference_list_is_read_only_to_authenticated_users(self):
        PersonAttributeType.objects.create(name="Occupation", format="java.lang.String")
        resp = self.client.get("/api/v1/person-attribute-types/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_unprivileged_user_cannot_edit_address(self):
        plain = User.objects.create_user("plain", "plain@x.io", "pw-strong-123")
        self.client.force_authenticate(plain)
        resp = self.client.post("/api/v1/person-addresses/", {
            "person": self.person.id, "address1": "123 Main St",
        }, format="json")
        self.assertEqual(resp.status_code, 403)
