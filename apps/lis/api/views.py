from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.emr.services import next_order_number
from apps.lis import models as m
from apps.lis import services
from apps.lis.api.serializers import (
    AnalyzerMessageSerializer,
    AnalyzerSerializer,
    IngestMessageSerializer,
    LabResultSerializer,
    LabSectionSerializer,
    LabTestSerializer,
    SpecimenSerializer,
    SpecimenTypeSerializer,
    TestOrderSerializer,
)
from apps.tenancy.mixins import TenantScopedQuerySetMixin
from django.utils import timezone


class LabSectionViewSet(viewsets.ModelViewSet):
    queryset = m.LabSection.objects.all()
    serializer_class = LabSectionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class SpecimenTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Reference list of specimen types for accessioning forms."""

    queryset = m.SpecimenType.objects.filter(retired=False).order_by("name")
    serializer_class = SpecimenTypeSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = m.LabTest.objects.select_related("section", "specimen_type", "concept")
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "test_code", "loinc_code"]
    filterset_fields = ["section", "is_panel"]


class TestOrderViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.TestOrder.objects.select_related("patient", "lab_test", "orderer")
    serializer_class = TestOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "lab_test", "fulfiller_status"]

    def perform_create(self, serializer):
        """Create a lab order, deriving the EMR Order plumbing from the test.

        A client only needs to supply ``patient`` and ``lab_test``; the order
        type ("Test Order"), the ordered ``concept`` (the test's concept), the
        activation time and the ordering provider are filled in here.
        """
        from apps.emr.models import OrderType

        lab_test = serializer.validated_data["lab_test"]
        extra = {"order_number": next_order_number()}
        if not serializer.validated_data.get("order_type"):
            extra["order_type"] = OrderType.objects.filter(name="Test Order").first()
        if not serializer.validated_data.get("concept"):
            extra["concept"] = lab_test.concept
        if not serializer.validated_data.get("date_activated"):
            extra["date_activated"] = timezone.now()
        if not serializer.validated_data.get("orderer"):
            provider = getattr(self.request.user, "provider", None)
            if provider is not None:
                extra["orderer"] = provider
        if not serializer.validated_data.get("specimen_source"):
            extra["specimen_source"] = lab_test.specimen_type
        serializer.save(**extra)

    @action(detail=True, methods=["post"])
    def worksheet(self, request, pk=None):
        """Generate the per-analyte result shells this order needs for entry.

        Idempotent: returns the order's full result set (creating any missing
        analyte rows), so the technologist always has a complete worksheet.
        """
        test_order = self.get_object()
        results = services.build_worksheet(test_order)
        return Response(LabResultSerializer(results, many=True).data)

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        """Download a patient-facing lab report PDF for this order."""
        from apps.lis.documents import build_lab_report_pdf

        test_order = self.get_object()
        pdf = build_lab_report_pdf(test_order)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="report_{test_order.order_number}.pdf"'
        )
        return response


class SpecimenViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Specimen.objects.select_related("patient", "specimen_type")
    serializer_class = SpecimenSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "status", "specimen_type"]

    def perform_create(self, serializer):
        """Accession a specimen, deriving its type from the linked order's test.

        A client supplies the ``patient`` and the ``orders`` being collected for;
        the specimen type is taken from the first order's test when not given.
        """
        extra = {"accession_number": services.next_accession_number()}
        if not serializer.validated_data.get("specimen_type"):
            orders = serializer.validated_data.get("orders") or []
            for order in orders:
                stype = order.lab_test.specimen_type
                if stype is not None:
                    extra["specimen_type"] = stype
                    break
        serializer.save(**extra)

    @action(detail=True, methods=["post"])
    def collect(self, request, pk=None):
        """Mark the specimen as collected, stamping the collection time."""
        specimen = self.get_object()
        specimen.status = m.Specimen.Status.COLLECTED
        specimen.collected_at = specimen.collected_at or timezone.now()
        provider = getattr(request.user, "provider", None)
        if provider and specimen.collected_by_id is None:
            specimen.collected_by = provider
        specimen.save(update_fields=["status", "collected_at", "collected_by", "changed_at"])
        return Response(self.get_serializer(specimen).data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """Mark the specimen as received in the lab, stamping the receipt time."""
        specimen = self.get_object()
        specimen.status = m.Specimen.Status.RECEIVED
        specimen.received_at = specimen.received_at or timezone.now()
        specimen.save(update_fields=["status", "received_at", "changed_at"])
        return Response(self.get_serializer(specimen).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject the specimen with a reason (e.g. haemolysed, insufficient)."""
        specimen = self.get_object()
        specimen.status = m.Specimen.Status.REJECTED
        specimen.rejection_reason = request.data.get("rejection_reason", "")
        specimen.save(update_fields=["status", "rejection_reason", "changed_at"])
        return Response(self.get_serializer(specimen).data)

    @action(detail=True, methods=["get"])
    def label(self, request, pk=None):
        """Download a printable specimen label PDF."""
        from apps.lis.documents import build_specimen_label_pdf

        specimen = self.get_object()
        pdf = build_specimen_label_pdf(specimen)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="label_{specimen.accession_number}.pdf"'
        )
        return response


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
    def auto_verify(self, request, pk=None):
        """Run the test's auto-verification rule on an entered result.

        Returns whether it was auto-verified and fires reflex orders if abnormal.
        """
        from apps.lis.automation_service import apply_reflex, auto_verify_result

        result = self.get_object()
        verified = auto_verify_result(result)
        reflex = apply_reflex(result)
        return Response({
            "auto_verified": verified,
            "status": result.status,
            "reflex_order": reflex.order_number if reflex else None,
        })

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


class AnalyzerMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """Inbound analyzer transmissions and their parse/match outcomes.

    POST ``ingest/`` to submit a raw HL7/ASTM payload for processing. This is the
    interface an instrument middleware or driver process calls to push results.
    """

    queryset = m.AnalyzerMessage.objects.select_related("analyzer")
    serializer_class = AnalyzerMessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["analyzer", "protocol", "status"]

    @action(detail=False, methods=["post"])
    def ingest(self, request):
        form = IngestMessageSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        from apps.lis.ingest import ingest_message

        message = ingest_message(
            form.validated_data["raw_payload"],
            protocol=form.validated_data["protocol"],
            analyzer=form.validated_data.get("analyzer"),
        )
        return Response(
            AnalyzerMessageSerializer(message).data, status=status.HTTP_201_CREATED
        )
