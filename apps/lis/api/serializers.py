from rest_framework import serializers

from apps.lis import models as m


class LabSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LabSection
        fields = ["id", "uuid", "name", "description", "location", "retired"]
        read_only_fields = ["uuid", "retired"]


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LabTest
        fields = ["id", "uuid", "name", "test_code", "concept", "section", "specimen_type",
                  "is_panel", "analytes", "turnaround_hours", "price", "loinc_code", "retired"]
        read_only_fields = ["uuid", "retired"]


class TestOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.TestOrder
        fields = ["id", "uuid", "order_number", "order_type", "concept", "patient", "encounter",
                  "orderer", "lab_test", "specimen_source", "clinical_history", "urgency",
                  "date_activated", "fulfiller_status", "voided"]
        read_only_fields = ["uuid", "order_number", "voided"]


class SpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Specimen
        fields = ["id", "uuid", "accession_number", "patient", "specimen_type", "orders",
                  "status", "collected_at", "collected_by", "received_at", "rejection_reason"]
        read_only_fields = ["uuid", "accession_number"]


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
