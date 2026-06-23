from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.emr.services import next_order_number
from apps.inventory.services import InsufficientStock
from apps.pharmacy import models as m
from apps.pharmacy import services
from apps.pharmacy.api.serializers import DispenseSerializer, DrugOrderSerializer
from apps.tenancy.mixins import TenantScopedQuerySetMixin


def _allergy_payload(allergies):
    """Serialise matched allergies for an API warning."""
    return [
        {
            "id": a.id,
            "allergen": a.allergen.name if a.allergen_id else "",
            "severity": a.severity,
            "reaction": a.reaction,
            "match_reason": getattr(a, "match_reason", "exact"),
        }
        for a in allergies
    ]


class DrugOrderViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.DrugOrder.objects.select_related("patient", "drug", "orderer")
    serializer_class = DrugOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["patient", "drug", "fulfiller_status"]

    @action(detail=False, methods=["get"])
    def allergy_check(self, request):
        """GET ?patient=&drug= -> documented drug allergies that match the drug.

        Lets the prescribing UI warn before submitting; an empty list means no
        documented allergy to this drug.
        """
        from apps.emr.models import Patient
        from apps.inventory.models import Product

        patient = Patient.objects.filter(pk=request.query_params.get("patient")).first()
        product = Product.objects.filter(pk=request.query_params.get("drug")).first()
        allergies = services.check_drug_allergies(patient, product)
        return Response({"allergies": _allergy_payload(allergies)})

    @action(detail=True, methods=["post"])
    def discontinue(self, request, pk=None):
        """Stop an active prescription (OpenMRS DISCONTINUE order action)."""
        order = self.get_object()
        if not order.is_active:
            raise ValidationError("This prescription is already inactive.")
        order.order_action = order.Action.DISCONTINUE
        order.date_stopped = timezone.now()
        reason = request.data.get("reason", "")
        if reason:
            order.fulfiller_comment = reason
        order.save(update_fields=["order_action", "date_stopped", "fulfiller_comment", "changed_at"])
        return Response(self.get_serializer(order).data)

    def perform_create(self, serializer):
        """Create a prescription, deriving the EMR Order plumbing from the drug.

        A client supplies ``patient`` and ``drug`` (plus dosing); the order type
        ("Drug Order"), the ordered ``concept`` (the product's clinical drug
        concept), the activation time and the prescriber are filled in here.

        Prescribing is blocked when the patient has a documented allergy to the
        drug, unless the caller passes ``override_allergy=true`` (the override is
        audited via the order's fulfiller comment).
        """
        from apps.emr.models import OrderType

        drug = serializer.validated_data["drug"]
        patient = serializer.validated_data.get("patient")
        allergies = services.check_drug_allergies(patient, drug)
        override = str(self.request.data.get("override_allergy", "")).lower() in ("1", "true", "yes")
        if allergies and not override:
            raise ValidationError({
                "allergy": "Patient has a documented allergy to this drug.",
                "allergies": _allergy_payload(allergies),
            })

        extra = {"order_number": next_order_number()}
        if allergies and override:
            names = ", ".join(a.allergen.name for a in allergies if a.allergen_id)
            extra["fulfiller_comment"] = f"Allergy override: {names}"[:255]
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

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        """Return a dispensed item to stock and mark it RETURNED."""
        dispense = self.get_object()
        try:
            services.reverse_dispense(
                dispense,
                provider=getattr(request.user, "provider", None),
                note=request.data.get("note", ""),
            )
        except services.DispenseReversalError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(dispense).data, status=status.HTTP_200_OK)
