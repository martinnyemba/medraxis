from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.emr.services import next_order_number
from apps.lis import models as m
from apps.lis import services
from apps.lis.api.serializers import (
    AnalyzerSerializer,
    LabResultSerializer,
    LabSectionSerializer,
    LabTestSerializer,
    SpecimenSerializer,
    TestOrderSerializer,
)


class LabSectionViewSet(viewsets.ModelViewSet):
    queryset = m.LabSection.objects.all()
    serializer_class = LabSectionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = m.LabTest.objects.select_related("section", "specimen_type", "concept")
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "test_code", "loinc_code"]
    filterset_fields = ["section", "is_panel"]


class TestOrderViewSet(viewsets.ModelViewSet):
    queryset = m.TestOrder.objects.select_related("patient", "lab_test", "orderer")
    serializer_class = TestOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "lab_test", "fulfiller_status"]

    def perform_create(self, serializer):
        serializer.save(order_number=next_order_number())


class SpecimenViewSet(viewsets.ModelViewSet):
    queryset = m.Specimen.objects.select_related("patient", "specimen_type")
    serializer_class = SpecimenSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "status", "specimen_type"]

    def perform_create(self, serializer):
        serializer.save(accession_number=services.next_accession_number())


class LabResultViewSet(viewsets.ModelViewSet):
    """Result entry + technical verification + release.

    The verification "two-person rule" is enforced here: the verifier must be a
    different provider from the one who entered the result.
    """

    queryset = m.LabResult.objects.select_related("test_order", "analyte", "specimen")
    serializer_class = LabResultSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["test_order", "status", "flag"]

    def _provider(self):
        return getattr(self.request.user, "provider", None)

    @action(detail=True, methods=["post"])
    def enter(self, request, pk=None):
        result = self.get_object()
        if result.value_numeric is None and not result.value_text:
            raise ValidationError("A numeric or text value is required to enter a result.")
        services.enter_result(result, provider=self._provider())
        return Response(self.get_serializer(result).data)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        result = self.get_object()
        if result.status != m.LabResult.Status.ENTERED:
            raise ValidationError("Only entered results can be verified.")
        provider = self._provider()
        if provider and result.entered_by_id == provider.id:
            raise ValidationError("A result must be verified by a different provider (two-person rule).")
        services.verify_result(result, provider=provider)
        return Response(self.get_serializer(result).data)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        result = self.get_object()
        if result.status != m.LabResult.Status.VERIFIED:
            raise ValidationError("Only verified results can be released.")
        services.release_result(result)
        return Response(self.get_serializer(result).data, status=status.HTTP_200_OK)


class AnalyzerViewSet(viewsets.ModelViewSet):
    queryset = m.Analyzer.objects.select_related("section")
    serializer_class = AnalyzerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["section", "protocol"]
