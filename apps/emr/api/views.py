from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.emr import models as m
from apps.emr.api.serializers import (
    AllergySerializer,
    CohortMembershipSerializer,
    CohortSerializer,
    ConceptSerializer,
    ConditionSerializer,
    DiagnosisSerializer,
    DrugSerializer,
    EncounterSerializer,
    EncounterTypeSerializer,
    FormSerializer,
    LocationSerializer,
    ObsSerializer,
    OrderFrequencySerializer,
    OrderSerializer,
    PatientIdentifierSerializer,
    PatientIdentifierTypeSerializer,
    PatientProgramSerializer,
    PatientSerializer,
    PatientStateSerializer,
    PersonAddressSerializer,
    PersonAttributeSerializer,
    PersonAttributeTypeSerializer,
    PersonNameSerializer,
    ProgramSerializer,
    ProgramWorkflowSerializer,
    ProgramWorkflowStateSerializer,
    RelationshipSerializer,
    RelationshipTypeSerializer,
    VisitSerializer,
    VisitTypeSerializer,
)
from apps.emr.services import next_order_number
from apps.tenancy.mixins import TenantScopedQuerySetMixin
from apps.users.permissions import HasPrivilege


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = m.Concept.objects.select_related("concept_class", "datatype")
    serializer_class = ConceptSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Concepts", "write": "Manage Concepts"}
    search_fields = ["name", "short_name"]
    filterset_fields = ["concept_class", "datatype", "is_set"]


class PatientViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = (
        m.Patient.objects.select_related("person")
        .prefetch_related("person__names", "identifiers__identifier_type")
    )
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Patients", "write": "Add Patients"}
    search_fields = [
        "identifiers__identifier",
        "person__names__given_name",
        "person__names__family_name",
    ]
    filterset_fields = {"person__gender": ["exact"], "person__dead": ["exact"]}


class VisitTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of visit types (Outpatient, Inpatient, ...) for forms."""

    queryset = m.VisitType.objects.filter(retired=False).order_by("name")
    serializer_class = VisitTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class EncounterTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of encounter types for forms."""

    queryset = m.EncounterType.objects.filter(retired=False).order_by("name")
    serializer_class = EncounterTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class LocationViewSet(TenantScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    """Reference list of facility locations for forms (tenant-scoped)."""

    queryset = m.Location.objects.filter(retired=False).order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class VisitViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Visit.objects.select_related("patient", "visit_type", "location")
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Visits", "write": "Manage Visits"}
    filterset_fields = ["patient", "visit_type", "location"]


class EncounterViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Encounter.objects.select_related(
        "patient", "encounter_type", "visit", "location"
    )
    serializer_class = EncounterSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Encounters", "write": "Manage Encounters"}
    filterset_fields = ["patient", "encounter_type", "visit", "location"]


class ObsViewSet(viewsets.ModelViewSet):
    queryset = m.Obs.objects.select_related("person", "concept", "encounter")
    serializer_class = ObsSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Observations", "write": "Add Observations"}
    filterset_fields = ["person", "concept", "encounter", "interpretation", "status"]


class AllergyViewSet(viewsets.ModelViewSet):
    queryset = m.Allergy.objects.select_related("allergen").prefetch_related("reactions")
    serializer_class = AllergySerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Clinical Records", "write": "Manage Clinical Records"}
    filterset_fields = ["patient", "category", "severity"]


class ConditionViewSet(viewsets.ModelViewSet):
    queryset = m.Condition.objects.select_related("concept")
    serializer_class = ConditionSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Clinical Records", "write": "Manage Clinical Records"}
    filterset_fields = ["patient", "clinical_status"]


class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = m.Diagnosis.objects.select_related("diagnosis_concept", "encounter")
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Clinical Records", "write": "Manage Clinical Records"}
    filterset_fields = ["patient", "encounter", "certainty"]


class OrderViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Order.objects.select_related(
        "order_type", "concept", "patient", "orderer"
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Orders", "write": "Manage Orders"}
    filterset_fields = ["patient", "order_type", "fulfiller_status", "urgency"]

    def perform_create(self, serializer):
        serializer.save(order_number=next_order_number())


class RelationshipTypeViewSet(viewsets.ModelViewSet):
    queryset = m.RelationshipType.objects.all()
    serializer_class = RelationshipTypeSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Relationships", "write": "Manage Relationships"}
    search_fields = ["name", "a_is_to_b", "b_is_to_a"]


class RelationshipViewSet(viewsets.ModelViewSet):
    queryset = m.Relationship.objects.select_related(
        "person_a", "person_b", "relationship_type")
    serializer_class = RelationshipSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Relationships", "write": "Manage Relationships"}
    filterset_fields = ["person_a", "person_b", "relationship_type"]


class DrugViewSet(viewsets.ModelViewSet):
    queryset = m.Drug.objects.select_related("concept", "dosage_form")
    serializer_class = DrugSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Drug Catalog", "write": "Manage Drug Catalog"}
    search_fields = ["name", "strength"]
    filterset_fields = ["concept", "combination"]


class OrderFrequencyViewSet(viewsets.ModelViewSet):
    queryset = m.OrderFrequency.objects.select_related("concept")
    serializer_class = OrderFrequencySerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Drug Catalog", "write": "Manage Drug Catalog"}
    search_fields = ["name"]


class CohortViewSet(viewsets.ModelViewSet):
    queryset = m.Cohort.objects.all()
    serializer_class = CohortSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Cohorts", "write": "Manage Cohorts"}
    search_fields = ["name"]


class CohortMembershipViewSet(viewsets.ModelViewSet):
    queryset = m.CohortMembership.objects.select_related("cohort", "patient")
    serializer_class = CohortMembershipSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Cohorts", "write": "Manage Cohorts"}
    filterset_fields = ["cohort", "patient"]


class FormViewSet(viewsets.ModelViewSet):
    queryset = m.Form.objects.select_related("encounter_type")
    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Forms", "write": "Manage Forms"}
    search_fields = ["name"]
    filterset_fields = ["published", "encounter_type"]


class PersonNameViewSet(viewsets.ModelViewSet):
    """Lets a person's names be added/edited after initial registration."""

    queryset = m.PersonName.objects.select_related("person")
    serializer_class = PersonNameSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Patients", "write": "Edit Patients"}
    filterset_fields = ["person"]


class PatientIdentifierViewSet(viewsets.ModelViewSet):
    """Lets a patient's identifiers be added/edited after initial registration."""

    queryset = m.PatientIdentifier.objects.select_related("identifier_type", "patient")
    serializer_class = PatientIdentifierSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Patients", "write": "Edit Patients"}
    filterset_fields = ["patient", "identifier_type"]


class PatientIdentifierTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of identifier types (Hospital No, NHIMA, ...) for forms."""

    queryset = m.PatientIdentifierType.objects.filter(retired=False).order_by("name")
    serializer_class = PatientIdentifierTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class PersonAddressViewSet(viewsets.ModelViewSet):
    queryset = m.PersonAddress.objects.select_related("person")
    serializer_class = PersonAddressSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Patients", "write": "Edit Patients"}
    filterset_fields = ["person"]


class PersonAttributeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of custom person-attribute definitions for forms."""

    queryset = m.PersonAttributeType.objects.filter(retired=False).order_by("sort_weight", "name")
    serializer_class = PersonAttributeTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class PersonAttributeViewSet(viewsets.ModelViewSet):
    queryset = m.PersonAttribute.objects.select_related("person", "attribute_type")
    serializer_class = PersonAttributeSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Patients", "write": "Edit Patients"}
    filterset_fields = ["person", "attribute_type"]


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of care programs (e.g. HIV, TB, ANC) for enrolment forms."""

    queryset = m.Program.objects.filter(retired=False).select_related("concept")
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class ProgramWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.ProgramWorkflow.objects.filter(retired=False).select_related("program")
    serializer_class = ProgramWorkflowSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["program"]


class ProgramWorkflowStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.ProgramWorkflowState.objects.filter(retired=False).select_related("workflow")
    serializer_class = ProgramWorkflowStateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["workflow"]


class PatientProgramViewSet(viewsets.ModelViewSet):
    """A patient's enrolment in a care program."""

    queryset = m.PatientProgram.objects.select_related("program", "location") \
        .prefetch_related("states__state")
    serializer_class = PatientProgramSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Programs", "write": "Manage Program Enrolment"}
    filterset_fields = ["patient", "program"]


class PatientStateViewSet(viewsets.ModelViewSet):
    """A period during which a program enrolment is in a particular state."""

    queryset = m.PatientState.objects.select_related("patient_program", "state")
    serializer_class = PatientStateSerializer
    permission_classes = [IsAuthenticated, HasPrivilege]
    required_privilege_map = {"read": "View Programs", "write": "Manage Program Enrolment"}
    filterset_fields = ["patient_program", "state"]
