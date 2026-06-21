from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments import models as m
from apps.payments import services
from apps.payments.api.serializers import (
    CreateIntentSerializer,
    PaymentGatewaySerializer,
    PaymentIntentSerializer,
)
from apps.payments.providers import PaymentError, get_provider
from apps.tenancy.mixins import TenantScopedQuerySetMixin


class PaymentGatewayViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.PaymentGateway.objects.select_related("settlement_account")
    serializer_class = PaymentGatewaySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["provider", "is_active", "is_test"]


class PaymentIntentViewSet(TenantScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = m.PaymentIntent.objects.select_related("gateway", "sale")
    serializer_class = PaymentIntentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["gateway", "status", "sale", "channel"]
    lookup_field = "reference"

    def create(self, request, *args, **kwargs):
        form = CreateIntentSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        d = form.validated_data
        try:
            intent = services.create_intent(
                gateway=d["gateway"], amount=d["amount"], currency=d.get("currency") or None,
                channel=d.get("channel"), sale=d.get("sale"),
                customer_email=d.get("customer_email", ""),
                customer_phone=d.get("customer_phone", ""),
                organization=getattr(request, "organization", None),
            )
        except PaymentError as exc:
            return Response({"error": {"status": 502, "type": "PaymentError",
                                       "detail": str(exc)}}, status=502)
        return Response(self.get_serializer(intent).data, status=status.HTTP_201_CREATED)

    # Allow POST on the collection while keeping reads read-only.
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def verify(self, request, reference=None):
        """Poll the provider for this intent's current status."""
        intent = self.get_object()
        provider = get_provider(intent.gateway)
        new_status = provider.verify(intent)
        if new_status == m.PaymentIntent.Status.SUCCEEDED:
            services.settle_intent(intent)
        elif new_status != intent.status:
            intent.status = new_status
            intent.save(update_fields=["status"])
        return Response(self.get_serializer(intent).data)
