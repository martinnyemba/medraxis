"""Point of Sale & business operations (Valeron/Vyapar-inspired).

A single ``Sale`` (invoice) can mix product lines (drawn from inventory) and
service lines (a consultation fee, a lab test, a procedure), which is exactly
what an integrated clinic/pharmacy/lab counter needs. Totals follow Vyapar-style
line-level tax and discount with GST-ready tax breakdown, and payments are
tracked separately so an invoice can be settled by cash, card, mobile money or
insurance -- or a split of them.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import models

from apps.core.models import TimeStampedModel

# Currency lines round half-up to the minor unit (standard invoicing convention).
_CENTS = Decimal("0.01")


def _money(value):
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


class Customer(TimeStampedModel):
    """A retail/walk-in customer. May be linked to an EMR patient."""

    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, blank=True, default="", db_index=True)
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    tax_identifier = models.CharField(max_length=64, blank=True, default="")
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.SET_NULL, null=True, blank=True, related_name="customers"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sale(TimeStampedModel):
    """An invoice / POS bill."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        COMPLETED = "COMPLETED", "Completed"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"
        REFUNDED = "REFUNDED", "Refunded"

    invoice_number = models.CharField(max_length=64, unique=True, db_index=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )
    location = models.ForeignKey(
        "emr.Location", on_delete=models.PROTECT, related_name="sales"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    cashier = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales"
    )

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["patient"]),
        ]

    def __str__(self):
        return self.invoice_number

    @property
    def balance_due(self):
        return self.grand_total - self.amount_paid

    def recalculate(self):
        """Recompute header totals from the lines (does not save)."""
        subtotal = Decimal("0")
        discount = Decimal("0")
        tax = Decimal("0")
        for line in self.lines.all():
            subtotal += line.gross_amount
            discount += line.discount_amount
            tax += line.tax_amount
        self.subtotal = subtotal
        self.discount_total = discount
        self.tax_total = tax
        self.grand_total = subtotal - discount + tax
        return self


class SaleLine(models.Model):
    """A single billed item -- a product, a lab test or an ad-hoc service."""

    class LineType(models.TextChoices):
        PRODUCT = "PRODUCT", "Product"
        SERVICE = "SERVICE", "Service"
        LAB_TEST = "LAB_TEST", "Lab test"
        CONSULTATION = "CONSULTATION", "Consultation"

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    line_type = models.CharField(
        max_length=20, choices=LineType.choices, default=LineType.PRODUCT
    )
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.PROTECT, null=True, blank=True, related_name="sale_lines"
    )
    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.PROTECT, null=True, blank=True, related_name="sale_lines"
    )
    description = models.CharField(max_length=255, blank=True, default="")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    issued_stock = models.BooleanField(
        default=False, help_text="True once this line has drawn down inventory."
    )

    class Meta:
        indexes = [models.Index(fields=["sale"])]

    def __str__(self):
        return self.description or (self.product and self.product.name) or "line"

    @property
    def gross_amount(self):
        return self.quantity * self.unit_price

    @property
    def discount_amount(self):
        return _money(self.gross_amount * self.discount_percent / Decimal("100"))

    @property
    def taxable_amount(self):
        return self.gross_amount - self.discount_amount

    @property
    def tax_amount(self):
        return _money(self.taxable_amount * self.tax_percent / Decimal("100"))

    @property
    def line_total(self):
        return self.taxable_amount + self.tax_amount


class Payment(TimeStampedModel):
    """A payment recorded against a sale."""

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile money"
        INSURANCE = "INSURANCE", "Insurance"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        CREDIT = "CREDIT", "Credit / account"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True, default="")
    received_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_received"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.amount} for {self.sale.invoice_number}"
