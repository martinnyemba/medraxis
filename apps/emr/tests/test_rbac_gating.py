"""RBAC enforcement tests for EMR ViewSets that gained privilege checks."""
from rest_framework.test import APITestCase

from apps.emr.models import (
    Cohort,
    Concept,
    ConceptClass,
    ConceptDatatype,
    Drug,
    Patient,
    PatientIdentifierType,
    Person,
    RelationshipType,
)
from apps.users.models import Privilege, Role, User


class RbacGatingTests(APITestCase):
    """A user with only read privileges can GET but not write; a user with
    no privileges at all gets 403 on both."""

    def setUp(self):
        PatientIdentifierType.objects.create(name="Medraxis ID", required=True)

        self.reader = User.objects.create_user("reader", "reader@x.io", "pw-strong-123")
        reader_role = Role.objects.create(name="Reader")
        reader_role.privileges.set([
            Privilege.objects.create(name="View Visits"),
            Privilege.objects.create(name="View Drug Catalog"),
            Privilege.objects.create(name="View Relationships"),
            Privilege.objects.create(name="View Cohorts"),
        ])
        self.reader.roles.add(reader_role)

        self.nobody = User.objects.create_user("nobody", "nobody@x.io", "pw-strong-123")

        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)

        cc = ConceptClass.objects.create(name="Drug")
        dt = ConceptDatatype.objects.create(name="Text")
        self.concept = Concept.objects.create(name="Amoxicillin", concept_class=cc, datatype=dt)

    def test_reader_can_list_visits_but_not_create(self):
        self.client.force_authenticate(self.reader)
        listed = self.client.get("/api/v1/visits/")
        self.assertEqual(listed.status_code, 200)

        created = self.client.post("/api/v1/visits/", {
            "patient": self.patient.id,
        }, format="json")
        self.assertEqual(created.status_code, 403)

    def test_nobody_cannot_list_visits(self):
        self.client.force_authenticate(self.nobody)
        resp = self.client.get("/api/v1/visits/")
        self.assertEqual(resp.status_code, 403)

    def test_reader_can_list_drugs_but_not_create(self):
        self.client.force_authenticate(self.reader)
        listed = self.client.get("/api/v1/drugs/")
        self.assertEqual(listed.status_code, 200)

        created = self.client.post("/api/v1/drugs/", {
            "name": "Paracetamol", "concept": self.concept.id,
        }, format="json")
        self.assertEqual(created.status_code, 403)

    def test_nobody_cannot_list_drugs(self):
        self.client.force_authenticate(self.nobody)
        resp = self.client.get("/api/v1/drugs/")
        self.assertEqual(resp.status_code, 403)

    def test_reader_can_list_relationship_types_but_not_create(self):
        self.client.force_authenticate(self.reader)
        listed = self.client.get("/api/v1/relationship-types/")
        self.assertEqual(listed.status_code, 200)

        created = self.client.post("/api/v1/relationship-types/", {
            "name": "Sibling", "a_is_to_b": "Sibling", "b_is_to_a": "Sibling",
        }, format="json")
        self.assertEqual(created.status_code, 403)

    def test_reader_can_list_cohorts_but_not_create(self):
        self.client.force_authenticate(self.reader)
        listed = self.client.get("/api/v1/cohorts/")
        self.assertEqual(listed.status_code, 200)

        created = self.client.post("/api/v1/cohorts/", {"name": "ART patients"}, format="json")
        self.assertEqual(created.status_code, 403)

    def test_drug_writer_can_create_drug(self):
        writer = User.objects.create_user("writer", "writer@x.io", "pw-strong-123")
        role = Role.objects.create(name="Pharmacist")
        view_priv, _ = Privilege.objects.get_or_create(name="View Drug Catalog")
        role.privileges.set([
            view_priv,
            Privilege.objects.create(name="Manage Drug Catalog"),
        ])
        writer.roles.add(role)
        self.client.force_authenticate(writer)

        resp = self.client.post("/api/v1/drugs/", {
            "name": "Paracetamol", "concept": self.concept.id,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(Drug.objects.count(), 1)
