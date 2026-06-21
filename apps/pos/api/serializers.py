from rest_framework import serializers

from apps.pos import models as m
from apps.pos.pricing import price_line


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Customer
        fields = ["id", "name", "phone", "email", "address", "tax_identifier", "patient"]


class SaleLineSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    discount_amount = serializers.ReadOnlyField()

    class Meta:
        model = m.SaleLine
        fields = ["id", "line_type", "product", "lab_test", "test_profile",
                  "billable_service", "description", "quantity", "unit_price",
                  "discount_percent", "tax_percent", "issued_stock",
                  "discount_amount", "tax_amount", "line_total"]
        read_only_fields = ["issued_stock"]
        extra_kwargs = {
            # Left unset, these resolve from the catalogue (see pricing.price_line).
            "unit_price": {"required": False},
            "tax_percent": {"required": False},
        }


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Payment
        fields = ["id", "sale", "method", "status", "amount", "reference",
                  "received_by", "created_at"]
        read_only_fields = ["status", "created_at"]


class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True)
    payments = PaymentSerializer(many=True, read_only=True)
    balance_due = serializers.ReadOnlyField()

    class Meta:
        model = m.Sale
        fields = ["id", "invoice_number", "customer", "client", "patient", "location",
                  "status", "cashier", "subtotal", "discount_total", "tax_total",
                  "grand_total", "amount_paid", "balance_due", "currency", "note",
                  "lines", "payments", "created_at"]
        read_only_fields = ["invoice_number", "subtotal", "discount_total", "tax_total",
                            "grand_total", "amount_paid", "balance_due", "created_at"]

    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        sale = m.Sale.objects.create(**validated_data)
        for line_data in lines:
            line = m.SaleLine(sale=sale, **line_data)
            # Resolve unit price / tax from the catalogue, honouring the client's
            # rate card, unless the caller supplied explicit values.
            price_line(line, client=sale.client)
            line.save()
        sale.recalculate()
        sale.save()
        return sale
