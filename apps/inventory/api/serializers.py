from rest_framework import serializers

from apps.emr.models import Location
from apps.inventory import models as m


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.UnitOfMeasure
        fields = ["id", "uuid", "name", "description", "retired"]
        read_only_fields = ["uuid", "retired"]


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductCategory
        fields = ["id", "uuid", "name", "parent", "description", "retired"]
        read_only_fields = ["uuid", "retired"]


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.TaxRate
        fields = ["id", "uuid", "name", "rate_percent", "hsn_sac_code", "retired"]
        read_only_fields = ["uuid", "retired"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Supplier
        fields = ["id", "uuid", "name", "contact_person", "phone", "email",
                  "address", "tax_identifier", "retired"]
        read_only_fields = ["uuid", "retired"]


class ProductSerializer(serializers.ModelSerializer):
    quantity_on_hand = serializers.ReadOnlyField()

    class Meta:
        model = m.Product
        fields = ["id", "uuid", "name", "sku", "barcode", "category", "unit", "tax_rate",
                  "drug_concept", "is_drug", "is_controlled", "strength", "sale_price",
                  "cost_price", "reorder_level", "track_batches", "track_expiry",
                  "quantity_on_hand", "retired"]
        read_only_fields = ["uuid", "retired", "quantity_on_hand"]


class StockBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = m.StockBatch
        fields = ["id", "product", "product_name", "location", "batch_number",
                  "expiry_date", "quantity_on_hand", "cost_price"]
        read_only_fields = fields


class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.StockTransaction
        fields = ["id", "product", "batch", "location", "transaction_type", "quantity",
                  "unit_cost", "reference_type", "reference_id", "note", "created_at"]
        read_only_fields = fields


class ReceiveStockSerializer(serializers.Serializer):
    """Input for the stock receipt action."""

    product = serializers.PrimaryKeyRelatedField(queryset=m.Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    batch_number = serializers.CharField(required=False, allow_blank=True, default="")
    expiry_date = serializers.DateField(required=False, allow_null=True)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PurchaseOrderItem
        fields = ["id", "product", "quantity_ordered", "quantity_received", "unit_cost"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)

    class Meta:
        model = m.PurchaseOrder
        fields = ["id", "po_number", "supplier", "location", "status",
                  "expected_date", "notes", "items"]
        read_only_fields = ["po_number"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        po = m.PurchaseOrder.objects.create(**validated_data)
        for item in items:
            m.PurchaseOrderItem.objects.create(purchase_order=po, **item)
        return po


class PurchaseBillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PurchaseBillItem
        fields = ["id", "product", "quantity", "unit_cost", "tax_percent",
                  "batch_number", "expiry_date"]


class PurchaseBillSerializer(serializers.ModelSerializer):
    items = PurchaseBillItemSerializer(many=True)
    balance_due = serializers.ReadOnlyField()
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    location_name = serializers.ReadOnlyField(source="location.name", default="")

    class Meta:
        model = m.PurchaseBill
        fields = ["id", "bill_number", "supplier", "supplier_name", "purchase_order", "location",
                  "location_name", "bill_date", "supplier_invoice_no", "subtotal", "tax_total",
                  "grand_total", "amount_paid", "balance_due", "status", "note", "items"]
        read_only_fields = ["bill_number", "subtotal", "tax_total", "grand_total",
                            "amount_paid", "balance_due", "status"]
        extra_kwargs = {"bill_date": {"required": False}}
