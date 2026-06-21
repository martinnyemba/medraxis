from rest_framework import serializers

from apps.pharmacy import models as m


class DrugOrderSerializer(serializers.ModelSerializer):
    quantity_dispensed = serializers.ReadOnlyField()

    class Meta:
        model = m.DrugOrder
        fields = ["id", "uuid", "order_number", "order_type", "concept", "patient", "encounter",
                  "orderer", "drug", "dose", "dose_units", "frequency", "route", "duration",
                  "duration_units", "quantity", "num_refills", "as_needed",
                  "dosing_instructions", "date_activated", "fulfiller_status",
                  "quantity_dispensed", "voided"]
        read_only_fields = ["uuid", "order_number", "voided", "quantity_dispensed"]


class DispenseSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = m.Dispense
        fields = ["id", "drug_order", "patient", "product", "location", "quantity",
                  "unit_price", "dispensed_by", "status", "note", "line_total", "created_at"]
        read_only_fields = ["line_total", "created_at"]
