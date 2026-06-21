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
    class Meta:
        model = m.PatientInsurance
        fields = ["id", "patient", "scheme", "policy_number", "valid_from",
                  "valid_to", "is_active"]
