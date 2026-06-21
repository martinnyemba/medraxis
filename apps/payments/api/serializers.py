from rest_framework import serializers

from apps.pos.models import Sale
from apps.payments import models as m


class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PaymentGateway
        fields = ["id", "uuid", "name", "provider", "is_active", "is_test", "currency",
                  "supported_channels", "settlement_account", "config", "retired"]
        read_only_fields = ["uuid", "retired"]
        # Never expose anything secret; config holds non-secret values only.


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PaymentIntent
        fields = ["id", "reference", "gateway", "sale", "amount", "currency", "channel",
                  "status", "customer_email", "customer_phone", "provider_reference",
                  "checkout_url", "failure_reason", "created_at"]
        read_only_fields = ["reference", "status", "provider_reference", "checkout_url",
                            "failure_reason", "created_at"]


class CreateIntentSerializer(serializers.Serializer):
    gateway = serializers.PrimaryKeyRelatedField(queryset=m.PaymentGateway.objects.all())
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    currency = serializers.CharField(required=False, allow_blank=True)
    channel = serializers.ChoiceField(choices=m.Channel.choices, required=False)
    sale = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(), required=False, allow_null=True,
    )
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
