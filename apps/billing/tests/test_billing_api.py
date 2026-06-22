"""CRUD and permission tests for the billing API (services, insurance)."""
from decimal import Decimal

from rest_framework.test import APITestCase

from apps.billing.models import BillableService, InsuranceScheme, PatientInsurance
from apps.emr.models import Patient, Person, PersonName
from apps.users.models import User


class BillableServiceApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("billing-u", "b@x.io", "pw-strong-123")

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/v1/billing/services/")
        self.assertEqual(resp.status_code, 401)

    def test_create_and_list(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post("/api/v1/billing/services/", {
            "name": "Consultation", "service_code": "CONS", "price": "100.00",
        })
        self.assertEqual(resp.status_code, 201, resp.content)

        resp = self.client.get("/api/v1/billing/services/")
        self.assertEqual(resp.data["count"], 1)

    def test_search_by_name(self):
        self.client.force_authenticate(self.user)
        BillableService.objects.create(name="X-Ray", service_code="XRAY", price=Decimal("50"))
        BillableService.objects.create(name="Consultation", service_code="CONS", price=Decimal("20"))

        resp = self.client.get("/api/v1/billing/services/", {"search": "X-Ray"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["service_code"], "XRAY")


class InsuranceSchemeApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("insurance-u", "i@x.io", "pw-strong-123")

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/v1/billing/insurance-schemes/")
        self.assertEqual(resp.status_code, 401)

    def test_create_and_list(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post("/api/v1/billing/insurance-schemes/", {
            "name": "NHIMA", "payer_name": "National Health Insurance",
            "coverage_percent": "80.00",
        })
        self.assertEqual(resp.status_code, 201, resp.content)

        resp = self.client.get("/api/v1/billing/insurance-schemes/")
        self.assertEqual(resp.data["count"], 1)


class PatientInsuranceApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("pi-u", "pi@x.io", "pw-strong-123")
        person = Person.objects.create(gender="F")
        PersonName.objects.create(person=person, given_name="Jane", family_name="Mwale", preferred=True)
        self.patient = Patient.objects.create(person=person)
        self.scheme = InsuranceScheme.objects.create(name="NHIMA", coverage_percent=Decimal("80"))

    def test_create_includes_patient_and_scheme_name(self):
        self.client.force_authenticate(self.user)
        res = self.client.post("/api/v1/billing/patient-insurance/", {
            "patient": self.patient.id, "scheme": self.scheme.id, "policy_number": "NH-001",
        })
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.data["patient_name"], "Jane Mwale")
        self.assertEqual(res.data["scheme_name"], "NHIMA")

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/v1/billing/patient-insurance/")
        self.assertEqual(resp.status_code, 401)

    def test_create_and_filter_by_patient(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post("/api/v1/billing/patient-insurance/", {
            "patient": self.patient.id, "scheme": self.scheme.id,
            "policy_number": "NH-001",
        })
        self.assertEqual(resp.status_code, 201, resp.content)

        other_person = Person.objects.create(gender="M")
        other_patient = Patient.objects.create(person=other_person)
        PatientInsurance.objects.create(
            patient=other_patient, scheme=self.scheme, policy_number="NH-002")

        resp = self.client.get("/api/v1/billing/patient-insurance/", {"patient": self.patient.id})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["policy_number"], "NH-001")
