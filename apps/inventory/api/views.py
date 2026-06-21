from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inventory import models as m
from apps.inventory import services
from apps.inventory.api.serializers import (
    ProductCategorySerializer,
    ProductSerializer,
    PurchaseOrderSerializer,
    ReceiveStockSerializer,
    StockBatchSerializer,
    StockTransactionSerializer,
    SupplierSerializer,
    TaxRateSerializer,
)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = m.ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = m.TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = m.Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "contact_person", "phone", "tax_identifier"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = m.Product.objects.select_related("category", "unit", "tax_rate")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "sku", "barcode", "strength"]
    filterset_fields = ["category", "is_drug", "is_controlled"]

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Products at or below their reorder level."""
        products = [p for p in self.get_queryset() if p.quantity_on_hand <= p.reorder_level]
        page = self.paginate_queryset(products)
        serializer = self.get_serializer(page or products, many=True)
        return self.get_paginated_response(serializer.data) if page is not None \
            else Response(serializer.data)

    @action(detail=False, methods=["post"])
    def receive(self, request):
        """Receive stock into a batch (writes a RECEIPT ledger entry)."""
        form = ReceiveStockSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        txn = services.receive_stock(
            product=form.validated_data["product"],
            location=form.validated_data["location"],
            quantity=form.validated_data["quantity"],
            unit_cost=form.validated_data.get("unit_cost") or 0,
            batch_number=form.validated_data.get("batch_number", ""),
            expiry_date=form.validated_data.get("expiry_date"),
            reference_type="MANUAL",
        )
        return Response(StockTransactionSerializer(txn).data)


class StockBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.StockBatch.objects.select_related("product", "location")
    serializer_class = StockBatchSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["product", "location"]
    ordering_fields = ["expiry_date", "quantity_on_hand"]

    @action(detail=False, methods=["get"])
    def expiring(self, request):
        days = int(request.query_params.get("days", 90))
        batches = services.expiring_soon(days=days)
        page = self.paginate_queryset(batches)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)


class StockTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.StockTransaction.objects.select_related("product", "batch", "location")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["product", "location", "transaction_type"]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = m.PurchaseOrder.objects.select_related("supplier", "location").prefetch_related("items")
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["supplier", "status", "location"]

    def perform_create(self, serializer):
        from apps.inventory.services_po import next_po_number
        serializer.save(po_number=next_po_number())
