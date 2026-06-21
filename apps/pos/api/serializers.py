from rest_framework import serializers

from apps.pos import models as m


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
        fields = ["id", "line_type", "product", "lab_test", "description", "quantity",
                  "unit_price", "discount_percent", "tax_percent", "issued_stock",
                  "discount_amount", "tax_amount", "line_total"]
        read_only_fields = ["issued_stock"]


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
        fields = ["id", "invoice_number", "customer", "patient", "location", "status",
                  "cashier", "subtotal", "discount_total", "tax_total", "grand_total",
                  "amount_paid", "balance_due", "currency", "note", "lines", "payments",
                  "created_at"]
        read_only_fields = ["invoice_number", "subtotal", "discount_total", "tax_total",
                            "grand_total", "amount_paid", "balance_due", "created_at"]

    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        sale = m.Sale.objects.create(**validated_data)
        for line in lines:
            m.SaleLine.objects.create(sale=sale, **line)
        sale.recalculate()
        sale.save()
        return sale
