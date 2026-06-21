"""API for the FLabs-inspired LIS extensions.

Serializers, viewsets and route registration for catalogue richness, B2B/multi-
branch, microbiology, QC, auto-verification and report delivery. Kept in its own
module to keep the original LIS API focused.
"""
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.lis import models as m
from apps.lis.delivery_service import dispatch_report


# --------------------------------------------------------------------------- #
# Serializers
# --------------------------------------------------------------------------- #
class TestMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.TestMethod
        fields = ["id", "uuid", "name", "lab_test", "instrument", "is_default", "retired"]
        read_only_fields = ["uuid", "retired"]


class ReferenceRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReferenceRange
        fields = ["id", "lab_test", "analyte", "method", "sex", "age_min_days",
                  "age_max_days", "low_normal", "hi_normal", "low_critical",
                  "hi_critical", "units", "text_range"]


class TestProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.TestProfile
        fields = ["id", "uuid", "name", "code", "price", "retired"]
        read_only_fields = ["uuid", "retired"]


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReportTemplate
        fields = ["id", "uuid", "name", "lab_test", "methodology_text",
                  "interpretation_template", "footer_notes", "is_default", "retired"]
        read_only_fields = ["uuid", "retired"]


class ReferringDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReferringDoctor
        fields = ["id", "uuid", "name", "code", "specialty", "phone", "email",
                  "hospital", "commission_percent", "retired"]
        read_only_fields = ["uuid", "retired"]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Client
        fields = ["id", "uuid", "name", "code", "client_type", "phone", "email",
                  "address", "credit_limit", "is_credit", "retired"]
        read_only_fields = ["uuid", "retired"]


class ReferenceLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReferenceLab
        fields = ["id", "uuid", "name", "code", "phone", "email", "address",
                  "default_tat_hours", "retired"]
        read_only_fields = ["uuid", "retired"]


class CollectionCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CollectionCenter
        fields = ["id", "uuid", "name", "code", "location", "processing_lab",
                  "phone", "is_home_collection", "retired"]
        read_only_fields = ["uuid", "retired"]


class CollectionAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CollectionAppointment
        fields = ["id", "patient", "collection_center", "scheduled_for",
                  "is_home_collection", "address", "phlebotomist", "status", "notes"]


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Organism
        fields = ["id", "uuid", "name", "code", "gram_stain", "retired"]
        read_only_fields = ["uuid", "retired"]


class AntibioticSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Antibiotic
        fields = ["id", "uuid", "name", "code", "abbreviation", "retired"]
        read_only_fields = ["uuid", "retired"]


class SensitivityResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.SensitivityResult
        fields = ["id", "antibiotic", "interpretation", "mic"]


class MicrobiologyResultSerializer(serializers.ModelSerializer):
    sensitivities = SensitivityResultSerializer(many=True, required=False)

    class Meta:
        model = m.MicrobiologyResult
        fields = ["id", "uuid", "test_order", "specimen", "growth", "organism",
                  "colony_count", "status", "comments", "sensitivities"]
        read_only_fields = ["uuid"]

    def create(self, validated_data):
        sens = validated_data.pop("sensitivities", [])
        result = m.MicrobiologyResult.objects.create(**validated_data)
        for s in sens:
            m.SensitivityResult.objects.create(microbiology_result=result, **s)
        return result


class QCMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.QCMaterial
        fields = ["id", "uuid", "name", "lot_number", "analyte", "analyzer", "level",
                  "target_mean", "target_sd", "units", "expiry_date", "retired"]
        read_only_fields = ["uuid", "retired"]


class QCResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.QCResult
        fields = ["id", "qc_material", "analyzer", "measured_value", "z_score",
                  "westgard_rule", "accepted", "run_at"]
        read_only_fields = ["z_score", "westgard_rule", "accepted"]


class AutoVerificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AutoVerificationRule
        fields = ["id", "uuid", "name", "lab_test", "enabled", "require_in_range",
                  "block_on_critical", "delta_check_percent", "reflex_on_abnormal", "retired"]
        read_only_fields = ["uuid", "retired"]


class ReportDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ReportDelivery
        fields = ["id", "test_order", "channel", "recipient_type", "recipient_address",
                  "status", "sent_at", "error", "created_at"]
        read_only_fields = ["status", "sent_at", "error", "created_at"]


# --------------------------------------------------------------------------- #
# ViewSets
# --------------------------------------------------------------------------- #
class _Auth(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]


class TestMethodViewSet(_Auth):
    queryset = m.TestMethod.objects.select_related("lab_test")
    serializer_class = TestMethodSerializer
    filterset_fields = ["lab_test"]


class ReferenceRangeViewSet(_Auth):
    queryset = m.ReferenceRange.objects.select_related("lab_test", "analyte")
    serializer_class = ReferenceRangeSerializer
    filterset_fields = ["lab_test", "analyte", "sex"]


class TestProfileViewSet(_Auth):
    queryset = m.TestProfile.objects.all()
    serializer_class = TestProfileSerializer
    search_fields = ["name", "code"]


class ReportTemplateViewSet(_Auth):
    queryset = m.ReportTemplate.objects.select_related("lab_test")
    serializer_class = ReportTemplateSerializer
    filterset_fields = ["lab_test"]


class ReferringDoctorViewSet(_Auth):
    queryset = m.ReferringDoctor.objects.all()
    serializer_class = ReferringDoctorSerializer
    search_fields = ["name", "code", "hospital"]


class ClientViewSet(_Auth):
    queryset = m.Client.objects.all()
    serializer_class = ClientSerializer
    search_fields = ["name", "code"]
    filterset_fields = ["client_type", "is_credit"]


class ReferenceLabViewSet(_Auth):
    queryset = m.ReferenceLab.objects.all()
    serializer_class = ReferenceLabSerializer
    search_fields = ["name", "code"]


class CollectionCenterViewSet(_Auth):
    queryset = m.CollectionCenter.objects.select_related("location", "processing_lab")
    serializer_class = CollectionCenterSerializer
    search_fields = ["name", "code"]


class CollectionAppointmentViewSet(_Auth):
    queryset = m.CollectionAppointment.objects.select_related(
        "patient", "collection_center", "phlebotomist")
    serializer_class = CollectionAppointmentSerializer
    filterset_fields = ["patient", "status", "is_home_collection", "collection_center"]


class OrganismViewSet(_Auth):
    queryset = m.Organism.objects.all()
    serializer_class = OrganismSerializer
    search_fields = ["name", "code"]


class AntibioticViewSet(_Auth):
    queryset = m.Antibiotic.objects.all()
    serializer_class = AntibioticSerializer
    search_fields = ["name", "code", "abbreviation"]


class MicrobiologyResultViewSet(_Auth):
    queryset = m.MicrobiologyResult.objects.select_related(
        "test_order", "organism").prefetch_related("sensitivities__antibiotic")
    serializer_class = MicrobiologyResultSerializer
    filterset_fields = ["test_order", "growth", "status"]


class QCMaterialViewSet(_Auth):
    queryset = m.QCMaterial.objects.select_related("analyte", "analyzer")
    serializer_class = QCMaterialSerializer
    filterset_fields = ["analyte", "analyzer"]


class QCResultViewSet(_Auth):
    queryset = m.QCResult.objects.select_related("qc_material", "analyzer")
    serializer_class = QCResultSerializer
    filterset_fields = ["qc_material", "accepted"]

    def perform_create(self, serializer):
        # Compute Z-score + Westgard evaluation on capture.
        instance = serializer.save()
        instance.compute()
        instance.save(update_fields=["z_score", "westgard_rule", "accepted"])


class AutoVerificationRuleViewSet(_Auth):
    queryset = m.AutoVerificationRule.objects.select_related("lab_test", "reflex_on_abnormal")
    serializer_class = AutoVerificationRuleSerializer
    filterset_fields = ["lab_test", "enabled"]


class ReportDeliveryViewSet(_Auth):
    queryset = m.ReportDelivery.objects.select_related("test_order")
    serializer_class = ReportDeliverySerializer
    filterset_fields = ["test_order", "channel", "status", "recipient_type"]

    def create(self, request, *args, **kwargs):
        """Dispatch a report over a channel (WhatsApp/SMS/email/portal)."""
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        delivery = dispatch_report(
            data["test_order"],
            channel=data.get("channel", m.ReportDelivery.Channel.WHATSAPP),
            recipient_type=data.get("recipient_type", m.ReportDelivery.Recipient.PATIENT),
            recipient_address=data.get("recipient_address", ""),
        )
        out = self.get_serializer(delivery)
        return Response(out.data, status=status.HTTP_201_CREATED)


def register_flabs_routes(router):
    router.register("lab/test-methods", TestMethodViewSet, basename="test-method")
    router.register("lab/reference-ranges", ReferenceRangeViewSet, basename="reference-range")
    router.register("lab/test-profiles", TestProfileViewSet, basename="test-profile")
    router.register("lab/report-templates", ReportTemplateViewSet, basename="report-template")
    router.register("lab/referring-doctors", ReferringDoctorViewSet, basename="referring-doctor")
    router.register("lab/clients", ClientViewSet, basename="lab-client")
    router.register("lab/reference-labs", ReferenceLabViewSet, basename="reference-lab")
    router.register("lab/collection-centers", CollectionCenterViewSet, basename="collection-center")
    router.register("lab/appointments", CollectionAppointmentViewSet, basename="collection-appointment")
    router.register("lab/organisms", OrganismViewSet, basename="organism")
    router.register("lab/antibiotics", AntibioticViewSet, basename="antibiotic")
    router.register("lab/microbiology-results", MicrobiologyResultViewSet, basename="microbiology-result")
    router.register("lab/qc-materials", QCMaterialViewSet, basename="qc-material")
    router.register("lab/qc-results", QCResultViewSet, basename="qc-result")
    router.register("lab/auto-verification-rules", AutoVerificationRuleViewSet, basename="auto-verification-rule")
    router.register("lab/report-deliveries", ReportDeliveryViewSet, basename="report-delivery")
