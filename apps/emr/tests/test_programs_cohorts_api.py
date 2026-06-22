"""API tests for program enrolment and cohort membership management."""
from rest_framework.test import APITestCase

from apps.emr.models import (
    Cohort,
    Patient,
    PatientIdentifierType,
    Person,
    Program,
    ProgramWorkflow,
    ProgramWorkflowState,
)
from apps.users.models import Privilege, Role, User


class ProgramsCohortsApiTests(APITestCase):
    def setUp(self):
        PatientIdentifierType.objects.create(name="Medraxis ID", required=True)

        self.user = User.objects.create_user("doc", "doc@x.io", "pw-strong-123")
        role = Role.objects.create(name="Clinician")
        role.privileges.set([
            Privilege.objects.create(name="View Programs"),
            Privilege.objects.create(name="Manage Program Enrolment"),
            Privilege.objects.create(name="View Cohorts"),
            Privilege.objects.create(name="Manage Cohorts"),
        ])
        self.user.roles.add(role)
        self.client.force_authenticate(self.user)

        person = Person.objects.create(gender="F")
        self.patient = Patient.objects.create(person=person)
        self.program = Program.objects.create(name="HIV Care and Treatment")
        workflow = ProgramWorkflow.objects.create(name="Treatment status", program=self.program)
        self.state = ProgramWorkflowState.objects.create(
            name="Active on ART", workflow=workflow, initial=True)

    def test_program_reference_list_is_visible(self):
        resp = self.client.get("/api/v1/programs/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_enrol_patient_in_program(self):
        resp = self.client.post("/api/v1/patient-programs/", {
            "patient": self.patient.id, "program": self.program.id,
            "date_enrolled": "2026-01-01",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["program_name"], "HIV Care and Treatment")

        enrolment_id = resp.data["id"]
        state_resp = self.client.post("/api/v1/patient-states/", {
            "patient_program": enrolment_id, "state": self.state.id,
            "start_date": "2026-01-01",
        }, format="json")
        self.assertEqual(state_resp.status_code, 201, state_resp.content)

        detail = self.client.get(f"/api/v1/patient-programs/{enrolment_id}/")
        self.assertEqual(len(detail.data["states"]), 1)
        self.assertEqual(detail.data["states"][0]["state_name"], "Active on ART")

    def test_create_cohort_and_add_member(self):
        resp = self.client.post("/api/v1/cohorts/", {"name": "ART patients"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        cohort_id = resp.data["id"]

        member_resp = self.client.post("/api/v1/cohort-memberships/", {
            "cohort": cohort_id, "patient": self.patient.id, "start_date": "2026-01-01",
        }, format="json")
        self.assertEqual(member_resp.status_code, 201, member_resp.content)

        cohort_detail = self.client.get(f"/api/v1/cohorts/{cohort_id}/")
        self.assertEqual(cohort_detail.data["member_count"], 1)

    def test_unprivileged_user_cannot_enrol_patient(self):
        plain = User.objects.create_user("plain", "plain@x.io", "pw-strong-123")
        self.client.force_authenticate(plain)
        resp = self.client.post("/api/v1/patient-programs/", {
            "patient": self.patient.id, "program": self.program.id,
            "date_enrolled": "2026-01-01",
        }, format="json")
        self.assertEqual(resp.status_code, 403)
