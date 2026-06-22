from rest_framework import serializers

from apps.lis import models as m


class LabSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LabSection
        fields = ["id", "uuid", "name", "description", "location", "retired"]
        read_only_fields = ["uuid", "retired"]


class SpecimenTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.SpecimenType
        fields = ["id", "uuid", "name", "description", "retired"]
        read_only_fields = fields


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LabTest
        fields = ["id", "uuid", "name", "test_code", "concept", "section", "specimen_type",
                  "is_panel", "analytes", "turnaround_hours", "price", "loinc_code", "retired"]
        read_only_fields = ["uuid", "retired"]


class TestOrderSerializer(serializers.ModelSerializer):
    lab_test_name = serializers.CharField(source="lab_test.name", read_only=True)

    class Meta:
        model = m.TestOrder
        fields = ["id", "uuid", "order_number", "order_type", "concept", "patient", "encounter",
                  "orderer", "lab_test", "lab_test_name", "specimen_source", "clinical_history",
                  "urgency", "date_activated", "fulfiller_status", "voided"]
        read_only_fields = ["uuid", "order_number", "voided"]
        extra_kwargs = {
            # Derived from the chosen lab test / request time when omitted
            # (see TestOrderViewSet.perform_create), so a lab order needs only a
            # patient and a test.
            "order_type": {"required": False},
            "concept": {"required": False},
            "date_activated": {"required": False},
        }


class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Specimen
        fields = ["id", "uuid", "accession_number", "patient", "specimen_type", "orders",
                  "status", "collected_at", "collected_by", "received_at", "rejection_reason"]
        read_only_fields = ["uuid", "accession_number"]
        # Derived from the linked order's test when omitted (see
        # SpecimenViewSet.perform_create).
        extra_kwargs = {"specimen_type": {"required": False}}


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LabResult
        fields = ["id", "uuid", "test_order", "specimen", "analyte", "value_numeric",
                  "value_text", "value_coded", "units", "reference_range", "flag", "status",
                  "entered_by", "entered_at", "verified_by", "verified_at", "analyzer", "obs"]
        read_only_fields = ["uuid", "flag", "status", "entered_at", "verified_at", "obs"]


class AnalyzerSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Analyzer
        fields = ["id", "uuid", "name", "section", "manufacturer", "model_number",
                  "protocol", "is_bidirectional", "retired"]
        read_only_fields = ["uuid", "retired"]


class AnalyzerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AnalyzerMessage
        fields = ["id", "analyzer", "protocol", "raw_payload", "status",
                  "results_matched", "results_unmatched", "log", "created_at"]
        read_only_fields = ["status", "results_matched", "results_unmatched",
                            "log", "created_at"]


class IngestMessageSerializer(serializers.Serializer):
    """Input for posting a raw analyzer transmission for ingestion."""

    protocol = serializers.ChoiceField(choices=["HL7", "ASTM"], default="HL7")
    raw_payload = serializers.CharField(style={"base_template": "textarea.html"})
    analyzer = serializers.PrimaryKeyRelatedField(
        queryset=m.Analyzer.objects.all(), required=False, allow_null=True
    )
