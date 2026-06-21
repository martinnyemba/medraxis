"""Inventory & stock control (Valeron/Vyapar-inspired).

A single product catalogue with batch- and expiry-tracked stock serves both
the pharmacy (drugs) and the POS (general goods/consumables). All stock
movement flows through an append-only :class:`StockTransaction` ledger, so the
quantity on hand is always reconcilable and auditable -- essential for
controlled drugs and for business accounting.
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel
from apps.tenancy.mixins import TenantScopedModel


class UnitOfMeasure(BaseOpenmrsMetadata):
    """Tablet, Bottle, Box, mL, mg, Strip, Piece, ..."""

    abbreviation = models.CharField(max_length=20, blank=True, default="")


class ProductCategory(BaseOpenmrsMetadata):
    """Hierarchical product grouping (Medicines > Antibiotics, Consumables, ...)."""

    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )

    class Meta:
        verbose_name_plural = "product categories"


class TaxRate(BaseOpenmrsMetadata):
    """A configurable tax (e.g. GST 5%/12%/18%, VAT) applied to sales lines."""

    rate_percent = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    hsn_sac_code = models.CharField(
        max_length=20, blank=True, default="", help_text="HSN/SAC code for GST compliance."
    )


class Supplier(BaseOpenmrsMetadata):
    """A vendor from whom stock is purchased."""

    contact_person = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    tax_identifier = models.CharField(max_length=64, blank=True, default="")


class Product(BaseOpenmrsMetadata, TenantScopedModel):
    """A sellable/dispensable item -- a drug, consumable or general good."""

    sku = models.CharField(max_length=64, unique=True, db_index=True)
    barcode = models.CharField(max_length=64, blank=True, default="", db_index=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT, related_name="products"
    )
    unit = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name="products"
    )
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    # Link to the clinical drug concept when the product is a medication.
    drug_concept = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    # Link to the specific clinical formulation (OpenMRS Drug), when applicable.
    drug = models.ForeignKey(
        "emr.Drug", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    is_drug = models.BooleanField(default=False)
    is_controlled = models.BooleanField(default=False, help_text="Controlled/scheduled drug.")
    strength = models.CharField(max_length=64, blank=True, default="")
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    track_batches = models.BooleanField(default=True)
    track_expiry = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["is_drug", "category"])]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def quantity_on_hand(self):
        agg = self.batches.aggregate(total=models.Sum("quantity_on_hand"))
        return agg["total"] or 0


class StockBatch(TimeStampedModel):
    """A batch/lot of a product at a location, with expiry and cost."""

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="batches")
    location = models.ForeignKey(
        "emr.Location", on_delete=models.PROTECT, related_name="stock_batches"
    )
    batch_number = models.CharField(max_length=64, blank=True, default="")
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    quantity_on_hand = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = "stock batches"
        ordering = ["expiry_date", "id"]
        unique_together = ("product", "location", "batch_number")
        indexes = [models.Index(fields=["product", "location", "expiry_date"])]

    def __str__(self):
        return f"{self.product.sku} / {self.batch_number or 'NOBATCH'} @ {self.location_id}"


class StockTransaction(TimeStampedModel):
    """An append-only ledger entry recording one stock movement.

    Quantity is signed: positive for receipts/returns, negative for issues and
    sales. The current quantity on a batch is the sum of its transactions.
    """

    class TxnType(models.TextChoices):
        RECEIPT = "RECEIPT", "Goods receipt"
        SALE = "SALE", "Sale / POS"
        DISPENSE = "DISPENSE", "Pharmacy dispense"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        TRANSFER_IN = "TRANSFER_IN", "Transfer in"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer out"
        RETURN = "RETURN", "Return"
        WASTAGE = "WASTAGE", "Wastage / expiry"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="transactions")
    batch = models.ForeignKey(
        StockBatch, on_delete=models.PROTECT, related_name="transactions", null=True, blank=True
    )
    location = models.ForeignKey(
        "emr.Location", on_delete=models.PROTECT, related_name="stock_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TxnType.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference_type = models.CharField(max_length=40, blank=True, default="")
    reference_id = models.CharField(max_length=64, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} x {self.product.sku}"


class PurchaseOrder(TimeStampedModel):
    """A purchase order raised to a supplier."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ORDERED = "ORDERED", "Ordered"
        PARTIAL = "PARTIAL", "Partially received"
        RECEIVED = "RECEIVED", "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    po_number = models.CharField(max_length=64, unique=True, db_index=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    location = models.ForeignKey(
        "emr.Location", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    """A line on a purchase order."""

    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_items")
    quantity_ordered = models.DecimalField(max_digits=14, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.sku} x {self.quantity_ordered}"
