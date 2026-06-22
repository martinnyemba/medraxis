from django.utils import timezone
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
        """Create a prescription, deriving the EMR Order plumbing from the drug.

        A client supplies ``patient`` and ``drug`` (plus dosing); the order type
        ("Drug Order"), the ordered ``concept`` (the product's clinical drug
        concept), the activation time and the prescriber are filled in here.
        """
        from apps.emr.models import OrderType

        drug = serializer.validated_data["drug"]
        extra = {"order_number": next_order_number()}
        if not serializer.validated_data.get("order_type"):
            extra["order_type"] = OrderType.objects.filter(name="Drug Order").first()
        if not serializer.validated_data.get("concept"):
            if drug.drug_concept_id is None:
                raise ValidationError(
                    {"drug": "This product has no clinical drug concept; set one on the "
                             "product before prescribing it."}
                )
            extra["concept"] = drug.drug_concept
        if not serializer.validated_data.get("date_activated"):
            extra["date_activated"] = timezone.now()
        if not serializer.validated_data.get("orderer"):
            provider = getattr(self.request.user, "provider", None)
            if provider is not None:
                extra["orderer"] = provider
        serializer.save(**extra)


class DispenseViewSet(viewsets.ModelViewSet):
    """Dispensing endpoint -- creation issues stock through the inventory ledger."""

    queryset = m.Dispense.objects.select_related("product", "patient", "drug_order")
    serializer_class = DispenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "product", "drug_order", "status"]

    def perform_create(self, serializer):
        data = serializer.validated_data
        drug_order = data.get("drug_order")
        # Dispensing against a prescription defaults the product/patient from it.
        product = data.get("product") or (drug_order.drug if drug_order else None)
        if product is None:
            raise ValidationError({"product": "A product is required."})
        patient = data.get("patient") or (drug_order.patient if drug_order else None)
        try:
            instance = services.dispense(
                product=product,
                location=data["location"],
                quantity=data["quantity"],
                patient=patient,
                drug_order=drug_order,
                provider=getattr(self.request.user, "provider", None),
                unit_price=data.get("unit_price"),
                note=data.get("note", ""),
            )
        except InsufficientStock as exc:
            raise ValidationError(str(exc))
        serializer.instance = instance
