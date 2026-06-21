from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.emr.services import next_order_number
from apps.inventory.services import InsufficientStock
from apps.pharmacy import models as m
from apps.pharmacy import services
from apps.pharmacy.api.serializers import DispenseSerializer, DrugOrderSerializer
from apps.tenancy.mixins import TenantScopedQuerySetMixin


class DrugOrderViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.DrugOrder.objects.select_related("patient", "drug", "orderer")
    serializer_class = DrugOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "drug", "fulfiller_status"]

    def perform_create(self, serializer):
        serializer.save(order_number=next_order_number())


class DispenseViewSet(viewsets.ModelViewSet):
    """Dispensing endpoint -- creation issues stock through the inventory ledger."""

    queryset = m.Dispense.objects.select_related("product", "patient", "drug_order")
    serializer_class = DispenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "product", "status"]

    def perform_create(self, serializer):
        data = serializer.validated_data
        try:
            instance = services.dispense(
                product=data["product"],
                location=data["location"],
                quantity=data["quantity"],
                patient=data.get("patient"),
                drug_order=data.get("drug_order"),
                provider=getattr(self.request.user, "provider", None),
                unit_price=data.get("unit_price"),
                note=data.get("note", ""),
            )
        except InsufficientStock as exc:
            raise ValidationError(str(exc))
        serializer.instance = instance
