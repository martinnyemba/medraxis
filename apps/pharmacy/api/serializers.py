from rest_framework import serializers

from apps.pharmacy import models as m


class DrugOrderSerializer(serializers.ModelSerializer):
    quantity_dispensed = serializers.ReadOnlyField()
    drug_name = serializers.CharField(source="drug.name", read_only=True)

    class Meta:
        model = m.DrugOrder
        fields = ["id", "uuid", "order_number", "order_type", "concept", "patient", "encounter",
                  "orderer", "drug", "drug_name", "dose", "dose_units", "frequency", "route",
                  "duration", "duration_units", "quantity", "num_refills", "as_needed",
                  "dosing_instructions", "date_activated", "fulfiller_status", "order_action",
                  "date_stopped", "fulfiller_comment", "quantity_dispensed", "voided"]
        read_only_fields = ["uuid", "order_number", "voided", "quantity_dispensed",
                            "order_action", "date_stopped"]
        # Derived from the chosen drug / request time when omitted (see
        # DrugOrderViewSet.perform_create), so a prescription needs only a
        # patient and a drug.
        extra_kwargs = {
            "order_type": {"required": False},
            "concept": {"required": False},
            "date_activated": {"required": False},
        }


class DispenseSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = m.Dispense
        fields = ["id", "drug_order", "patient", "product", "product_name", "location",
                  "quantity", "unit_price", "dispensed_by", "status", "note", "line_total",
                  "created_at"]
        read_only_fields = ["line_total", "created_at"]
        # When dispensing against a prescription, the product/patient default
        # from the order (see DispenseViewSet.perform_create).
        extra_kwargs = {"product": {"required": False}}
