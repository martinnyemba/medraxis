from rest_framework import serializers

from apps.billing import models as m


class BillableServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.BillableService
        fields = ["id", "uuid", "name", "service_code", "concept", "price", "tax_rate", "retired"]
        read_only_fields = ["uuid", "retired"]


class InsuranceSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.InsuranceScheme
        fields = ["id", "uuid", "name", "payer_name", "coverage_percent", "contact", "retired"]
        read_only_fields = ["uuid", "retired"]


class PatientInsuranceSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    scheme_name = serializers.ReadOnlyField(source="scheme.name")

    class Meta:
        model = m.PatientInsurance
        fields = ["id", "patient", "patient_name", "scheme", "scheme_name", "policy_number",
                  "valid_from", "valid_to", "is_active"]

    def get_patient_name(self, obj):
        name = obj.patient.person.preferred_name
        return str(name) if name else ""
