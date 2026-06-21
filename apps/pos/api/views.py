from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inventory.services import InsufficientStock
from apps.tenancy.mixins import TenantScopedQuerySetMixin
from apps.pos import models as m
from apps.pos import services
from apps.pos.api.serializers import CustomerSerializer, PaymentSerializer, SaleSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = m.Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "phone", "email", "tax_identifier"]


class SaleViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Sale.objects.select_related("customer", "patient", "location").prefetch_related(
        "lines", "payments"
    )
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "patient", "customer", "location"]
    search_fields = ["invoice_number"]

    def perform_create(self, serializer):
        serializer.save(
            invoice_number=services.next_invoice_number(),
            cashier=self.request.user if self.request.user.is_authenticated else None,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Finalise the sale and draw down stock for product lines."""
        sale = self.get_object()
        try:
            services.complete_sale(sale)
        except InsufficientStock as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(sale).data)

    @action(detail=True, methods=["post"])
    def reprice(self, request, pk=None):
        """Re-resolve catalogue prices for the sale's lines (e.g. after setting a client)."""
        sale = self.get_object()
        services.reprice_sale(sale)
        return Response(self.get_serializer(sale).data)

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        """Download the sale as a printable PDF invoice/receipt."""
        from apps.pos.documents import build_receipt_pdf

        sale = self.get_object()
        pdf = build_receipt_pdf(sale)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="receipt_{sale.invoice_number}.pdf"'
        )
        return response

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Record a payment against the sale."""
        sale = self.get_object()
        method = request.data.get("method", m.Payment.Method.CASH)
        amount = request.data.get("amount")
        if amount is None:
            raise ValidationError("'amount' is required.")
        services.add_payment(
            sale, method=method, amount=amount,
            reference=request.data.get("reference", ""),
            received_by=request.user if request.user.is_authenticated else None,
        )
        return Response(self.get_serializer(sale).data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.Payment.objects.select_related("sale")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sale", "method", "status"]
