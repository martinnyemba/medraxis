"""Financial / accounting backbone (Vyapar / Valeron-inspired).

Two append-only ledgers complement the existing stock ledger:

* the **money ledger** -- :class:`FinancialAccount` (cash/bank) with
  :class:`AccountTransaction` rows for every money movement; and
* the **party ledger** -- :class:`PartyLedgerEntry` giving each customer,
  supplier or B2B client a running receivable/payable balance.

Expenses, supplier payments and (via services) sales/purchases post into these,
so the platform tracks not just *what was sold* but *where the money is* and
*who owes whom*. See ``docs/business_ops_research.md``.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel
from apps.tenancy.mixins import TenantScopedModel


class TaxComponent(models.Model):
    """A component of a headline tax rate (e.g. GST 18% = CGST 9% + SGST 9%).

    Lets invoices show the compliant split while the parent ``TaxRate`` keeps the
    single headline percentage used for line maths.
    """

    class ComponentType(models.TextChoices):
        CGST = "CGST", "CGST"
        SGST = "SGST", "SGST"
        IGST = "IGST", "IGST"
        CESS = "CESS", "Cess"
        VAT = "VAT", "VAT"
        OTHER = "OTHER", "Other"

    tax_rate = models.ForeignKey(
        "inventory.TaxRate", on_delete=models.CASCADE, related_name="components"
    )
    component_type = models.CharField(max_length=10, choices=ComponentType.choices)
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["component_type"]

    def __str__(self):
        return f"{self.component_type} {self.rate_percent}%"


class FinancialAccount(BaseOpenmrsMetadata, TenantScopedModel):
    """A cash drawer or bank account that money flows through."""

    class AccountType(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK = "BANK", "Bank"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile money"
        CARD = "CARD", "Card settlement"

    account_type = models.CharField(
        max_length=20, choices=AccountType.choices, default=AccountType.CASH
    )
    account_number = models.CharField(max_length=64, blank=True, default="")
    bank_name = models.CharField(max_length=160, blank=True, default="")
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class AccountTransaction(TimeStampedModel):
    """One money movement in/out of a :class:`FinancialAccount` (append-only)."""

    class Direction(models.TextChoices):
        IN = "IN", "Money in"
        OUT = "OUT", "Money out"

    account = models.ForeignKey(
        FinancialAccount, on_delete=models.PROTECT, related_name="transactions"
    )
    direction = models.CharField(max_length=3, choices=Direction.choices)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    balance_after = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    reference_type = models.CharField(max_length=40, blank=True, default="")
    reference_id = models.CharField(max_length=64, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")
    occurred_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["account", "-occurred_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.direction} {self.amount} ({self.account_id})"


class ExpenseCategory(BaseOpenmrsMetadata):
    """A bucket for business costs: Rent, Salaries, Utilities, Reagents, ..."""

    class Meta:
        verbose_name_plural = "expense categories"
        ordering = ["name"]


class Expense(TimeStampedModel, TenantScopedModel):
    """A business cost (money out), optionally settled from an account."""

    number = models.CharField(max_length=64, unique=True, db_index=True)
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT, related_name="expenses"
    )
    account = models.ForeignKey(
        FinancialAccount, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expenses",
    )
    supplier = models.ForeignKey(
        "inventory.Supplier", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="expenses",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expense_date = models.DateField(db_index=True)
    payment_method = models.CharField(max_length=20, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-expense_date", "-id"]

    def __str__(self):
        return f"{self.number} {self.amount}"

    @property
    def total(self):
        return self.amount + self.tax_amount


class SupplierPayment(TimeStampedModel, TenantScopedModel):
    """A payment made to a supplier (money out / Payment-Out)."""

    number = models.CharField(max_length=64, unique=True, db_index=True)
    supplier = models.ForeignKey(
        "inventory.Supplier", on_delete=models.PROTECT, related_name="payments"
    )
    account = models.ForeignKey(
        FinancialAccount, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="supplier_payments",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_on = models.DateField(db_index=True)
    method = models.CharField(max_length=20, default="CASH")
    reference = models.CharField(max_length=120, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-paid_on", "-id"]

    def __str__(self):
        return f"{self.number} -> {self.supplier_id} {self.amount}"


class SupplierPaymentAllocation(models.Model):
    """Allocates a supplier payment to a specific purchase bill."""

    payment = models.ForeignKey(
        SupplierPayment, on_delete=models.CASCADE, related_name="allocations"
    )
    purchase_bill = models.ForeignKey(
        "inventory.PurchaseBill", on_delete=models.CASCADE, related_name="payment_allocations"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.amount} -> bill {self.purchase_bill_id}"


class PartyLedgerEntry(TimeStampedModel):
    """A running receivable/payable ledger line for any party.

    The *party* is a customer, supplier or B2B client (via a generic relation),
    so one ledger answers "what does this party owe / are they owed?" across
    sales, purchases, payments and returns.
    """

    class EntryType(models.TextChoices):
        OPENING = "OPENING", "Opening balance"
        INVOICE = "INVOICE", "Sale invoice"
        PAYMENT_IN = "PAYMENT_IN", "Payment received"
        PURCHASE_BILL = "PURCHASE_BILL", "Purchase bill"
        PAYMENT_OUT = "PAYMENT_OUT", "Payment made"
        CREDIT_NOTE = "CREDIT_NOTE", "Credit note (sales return)"
        DEBIT_NOTE = "DEBIT_NOTE", "Debit note (purchase return)"

    party_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    party_object_id = models.PositiveIntegerField()
    party = GenericForeignKey("party_content_type", "party_object_id")

    organization = models.ForeignKey(
        "tenancy.Organization", on_delete=models.CASCADE, null=True, blank=True,
        related_name="party_ledger_entries",
    )
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    entry_date = models.DateField(db_index=True)
    # Debit increases what the party owes us (receivable); credit decreases it.
    debit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    reference_type = models.CharField(max_length=40, blank=True, default="")
    reference_id = models.CharField(max_length=64, blank=True, default="")
    narration = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["party_content_type", "party_object_id", "entry_date", "id"]
        indexes = [
            models.Index(fields=["party_content_type", "party_object_id", "entry_date"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.entry_type} D{self.debit} C{self.credit} bal {self.balance}"
