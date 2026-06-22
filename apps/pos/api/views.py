from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inventory.services import InsufficientStock
from apps.pos import models as m
from apps.pos import services
from apps.pos.api.serializers import (
    CustomerSerializer,
    PaymentSerializer,
    QuotationSerializer,
    SaleSerializer,
    SalesReturnSerializer,
)
from apps.tenancy.mixins import TenantScopedQuerySetMixin


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
        extra = {
            "invoice_number": services.next_invoice_number(),
            "cashier": self.request.user if self.request.user.is_authenticated else None,
        }
        if not serializer.validated_data.get("location"):
            extra["location"] = self._default_location()
        serializer.save(**extra)

    def _default_location(self):
        """The active facility's location, used when a sale omits one.

        Prefers a location scoped to the active tenant, falling back to any
        location (reference locations seeded before tenancy have no org).
        """
        from apps.emr.models import Location

        base = Location.objects.filter(retired=False)
        org = getattr(self.request, "organization", None)
        if org is not None:
            scoped = base.filter(organization=org).first()
            if scoped is not None:
                return scoped
        return base.first()

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
        """Record a payment against the sale (optionally into a financial account)."""
        sale = self.get_object()
        method = request.data.get("method", m.Payment.Method.CASH)
        amount = request.data.get("amount")
        if amount is None:
            raise ValidationError("'amount' is required.")
        account = None
        account_id = request.data.get("account")
        if account_id:
            from apps.finance.models import FinancialAccount
            account = FinancialAccount.objects.filter(pk=account_id).first()
        services.add_payment(
            sale, method=method, amount=amount,
            reference=request.data.get("reference", ""),
            received_by=request.user if request.user.is_authenticated else None,
            account=account,
        )
        return Response(self.get_serializer(sale).data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.Payment.objects.select_related("sale")
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["sale", "method", "status"]


class QuotationViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Quotation.objects.select_related(
        "customer", "client", "patient", "location").prefetch_related("lines")
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "customer", "client", "patient"]
    search_fields = ["quotation_number"]

    def perform_create(self, serializer):
        serializer.save(quotation_number=services.next_quotation_number())

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Convert this quotation into a Sale."""
        quotation = self.get_object()
        sale = services.convert_quotation_to_sale(quotation)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SalesReturnViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.SalesReturn.objects.select_related("sale", "location").prefetch_related("lines")
    serializer_class = SalesReturnSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "sale"]

    def perform_create(self, serializer):
        serializer.save(return_number=services.next_return_number())

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Complete the return: restock goods and credit the party."""
        sales_return = self.get_object()
        services.process_sales_return(sales_return)
        return Response(self.get_serializer(sales_return).data)
