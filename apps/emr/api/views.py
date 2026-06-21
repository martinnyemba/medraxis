from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.emr import models as m
from apps.emr.api.serializers import (
    ConceptSerializer,
    EncounterSerializer,
    ObsSerializer,
    OrderSerializer,
    PatientSerializer,
    VisitSerializer,
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


class VisitViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Visit.objects.select_related("patient", "visit_type", "location")
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "visit_type", "location"]


class EncounterViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Encounter.objects.select_related(
        "patient", "encounter_type", "visit", "location"
    )
    serializer_class = EncounterSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "encounter_type", "visit", "location"]


class ObsViewSet(viewsets.ModelViewSet):
    queryset = m.Obs.objects.select_related("person", "concept", "encounter")
    serializer_class = ObsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["person", "concept", "encounter", "interpretation", "status"]


class OrderViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Order.objects.select_related(
        "order_type", "concept", "patient", "orderer"
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "order_type", "fulfiller_status", "urgency"]

    def perform_create(self, serializer):
        serializer.save(order_number=next_order_number())
