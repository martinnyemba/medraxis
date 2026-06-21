from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.billing import models as m
from apps.billing.api.serializers import (
    BillableServiceSerializer,
    InsuranceSchemeSerializer,
    PatientInsuranceSerializer,
)


class BillableServiceViewSet(viewsets.ModelViewSet):
    queryset = m.BillableService.objects.select_related("tax_rate")
    serializer_class = BillableServiceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "service_code"]


class InsuranceSchemeViewSet(viewsets.ModelViewSet):
    queryset = m.InsuranceScheme.objects.all()
    serializer_class = InsuranceSchemeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "payer_name"]


class PatientInsuranceViewSet(viewsets.ModelViewSet):
    queryset = m.PatientInsurance.objects.select_related("scheme", "patient")
    serializer_class = PatientInsuranceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "scheme", "is_active"]
