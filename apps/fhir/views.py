"""FHIR R4 REST facade.

Implements the read and search interactions for a curated set of resources::

    GET /fhir/metadata
    GET /fhir/{ResourceType}
    GET /fhir/{ResourceType}/{id}

Resources are projected from Medraxis models by :mod:`apps.fhir.mappers`.
Querysets are tenant-scoped when an organization is resolved for the request,
so FHIR clients see only their facility's data. This is a read facade; write
interactions are intentionally out of scope for this iteration.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fhir import mappers
from apps.tenancy.mixins import TenantResolverMixin, scope_to_current_organization


class FHIRResource:
    """Configuration for one exposed FHIR resource type."""

    def __init__(self, name, mapper, base_queryset, search):
        self.name = name
        self.mapper = mapper
        self.base_queryset = base_queryset
        self.search = search  # dict: fhir_param -> callable(queryset, value)


def _patient_qs():
    from apps.emr.models import Patient

    return Patient.objects.select_related("person").prefetch_related(
        "person__names", "identifiers__identifier_type"
    )


def _encounter_qs():
    from apps.emr.models import Encounter

    return Encounter.objects.select_related("patient", "encounter_type", "visit")


def _obs_qs():
    from apps.emr.models import Obs

    return Obs.objects.select_related("person", "concept", "encounter")


def _order_qs():
    from apps.emr.models import Order

    return Order.objects.select_related("patient", "concept")


def _drug_order_qs():
    from apps.pharmacy.models import DrugOrder

    return DrugOrder.objects.select_related(
        "patient", "drug", "drug_formulation__concept", "order_frequency")


def _test_order_qs():
    from apps.lis.models import TestOrder

    return TestOrder.objects.select_related("patient", "lab_test").prefetch_related("results__obs")


def _organization_qs():
    from apps.tenancy.models import Organization

    return Organization.objects.all()


def _patient_by_uuid(qs, value):
    return qs.filter(identifiers__identifier=value)


REGISTRY = {
    "Patient": FHIRResource(
        "Patient", mappers.patient_to_fhir, _patient_qs,
        {
            "identifier": lambda qs, v: qs.filter(identifiers__identifier=v),
            "name": lambda qs, v: qs.filter(person__names__family_name__icontains=v),
            "family": lambda qs, v: qs.filter(person__names__family_name__icontains=v),
            "gender": lambda qs, v: qs.filter(
                person__gender={"male": "M", "female": "F"}.get(v, v)),
        },
    ),
    "Encounter": FHIRResource(
        "Encounter", mappers.encounter_to_fhir, _encounter_qs,
        {"patient": lambda qs, v: qs.filter(patient__uuid=v),
         "subject": lambda qs, v: qs.filter(patient__uuid=v.split("/")[-1])},
    ),
    "Observation": FHIRResource(
        "Observation", mappers.obs_to_fhir, _obs_qs,
        {"patient": lambda qs, v: qs.filter(person__patient__uuid=v),
         "code": lambda qs, v: qs.filter(concept__name__icontains=v)},
    ),
    "ServiceRequest": FHIRResource(
        "ServiceRequest", mappers.service_request_to_fhir, _order_qs,
        {"patient": lambda qs, v: qs.filter(patient__uuid=v)},
    ),
    "MedicationRequest": FHIRResource(
        "MedicationRequest", mappers.medication_request_to_fhir, _drug_order_qs,
        {"patient": lambda qs, v: qs.filter(patient__uuid=v)},
    ),
    "DiagnosticReport": FHIRResource(
        "DiagnosticReport", mappers.diagnostic_report_to_fhir, _test_order_qs,
        {"patient": lambda qs, v: qs.filter(patient__uuid=v)},
    ),
    "Organization": FHIRResource(
        "Organization", mappers.organization_to_fhir, _organization_qs, {},
    ),
}

# Resources whose querysets carry their own organization FK and can be scoped.
TENANT_SCOPED = {"Patient", "Encounter", "ServiceRequest",
                 "MedicationRequest", "DiagnosticReport"}

FHIR_CONTENT_TYPE = "application/fhir+json"


class FHIRBaseView(TenantResolverMixin, APIView):
    permission_classes = [IsAuthenticated]

    def _scoped(self, resource, queryset):
        if resource.name in TENANT_SCOPED:
            return scope_to_current_organization(queryset)
        if resource.name == "Observation":
            from apps.tenancy.context import get_current_organization

            org = get_current_organization()
            if org is not None:
                return queryset.filter(person__patient__organization=org)
        return queryset


class FHIRSearchView(FHIRBaseView):
    def get(self, request, resource_type):
        resource = REGISTRY.get(resource_type)
        if resource is None:
            return self._not_supported(resource_type)

        queryset = self._scoped(resource, resource.base_queryset())
        for param, value in request.query_params.items():
            handler = resource.search.get(param)
            if handler is not None:
                queryset = handler(queryset, value)
        queryset = queryset.distinct()

        try:
            count = int(request.query_params.get("_count", 50))
        except ValueError:
            count = 50
        count = max(1, min(count, 200))

        total = queryset.count()
        resources = [resource.mapper(obj) for obj in queryset[:count]]
        return Response(
            mappers.bundle(resources, total=total), content_type=FHIR_CONTENT_TYPE
        )

    def _not_supported(self, resource_type):
        return Response(
            mappers.operation_outcome(
                "error", "not-supported", f"Resource type '{resource_type}' is not supported."
            ),
            status=status.HTTP_404_NOT_FOUND,
            content_type=FHIR_CONTENT_TYPE,
        )


class FHIRReadView(FHIRBaseView):
    def get(self, request, resource_type, resource_id):
        resource = REGISTRY.get(resource_type)
        if resource is None:
            return Response(
                mappers.operation_outcome("error", "not-supported",
                                          f"Resource type '{resource_type}' is not supported."),
                status=status.HTTP_404_NOT_FOUND, content_type=FHIR_CONTENT_TYPE,
            )

        queryset = self._scoped(resource, resource.base_queryset())
        lookup = "id" if resource_type == "Organization" else "uuid"
        obj = queryset.filter(**{lookup: resource_id}).first()
        if obj is None:
            return Response(
                mappers.operation_outcome("error", "not-found",
                                          f"{resource_type}/{resource_id} not found."),
                status=status.HTTP_404_NOT_FOUND, content_type=FHIR_CONTENT_TYPE,
            )
        return Response(resource.mapper(obj), content_type=FHIR_CONTENT_TYPE)


class FHIRCapabilityStatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        resources = [
            {"type": name, "interaction": [{"code": "read"}, {"code": "search-type"}]}
            for name in sorted(REGISTRY)
        ]
        return Response(
            {
                "resourceType": "CapabilityStatement",
                "status": "active",
                "fhirVersion": "4.0.1",
                "format": ["json"],
                "rest": [{"mode": "server", "resource": resources}],
            },
            content_type=FHIR_CONTENT_TYPE,
        )
