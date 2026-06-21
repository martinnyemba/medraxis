"""Pharmacy: prescribing and dispensing.

Prescriptions are EMR orders (:class:`DrugOrder` extends
:class:`~apps.emr.models.Order`), so they sit on the same patient timeline as
lab orders and consultations. Dispensing draws stock down through the shared
inventory ledger, linking the clinical act (what was prescribed) to the
business act (what left the shelf, from which batch, at what price).
"""
from django.db import models

from apps.core.models import TimeStampedModel
from apps.emr.models import Order


class DrugOrder(Order):
    """A medication order / prescription line."""

    class DurationUnit(models.TextChoices):
        DAYS = "DAYS", "Days"
        WEEKS = "WEEKS", "Weeks"
        MONTHS = "MONTHS", "Months"

    drug = models.ForeignKey(
        "inventory.Product", on_delete=models.PROTECT, related_name="drug_orders"
    )
    dose = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dose_units = models.CharField(max_length=50, blank=True, default="")
    frequency = models.CharField(
        max_length=50, blank=True, default="", help_text="e.g. BD, TDS, QID, OD"
    )
    route = models.CharField(max_length=50, blank=True, default="", help_text="PO, IV, IM, ...")
    duration = models.PositiveIntegerField(null=True, blank=True)
    duration_units = models.CharField(
        max_length=20, choices=DurationUnit.choices, blank=True, default=""
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    num_refills = models.PositiveSmallIntegerField(default=0)
    as_needed = models.BooleanField(default=False)
    dosing_instructions = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "drug order"

    @property
    def quantity_dispensed(self):
        agg = self.dispenses.aggregate(total=models.Sum("quantity"))
        return agg["total"] or 0


class Dispense(TimeStampedModel):
    """A dispensing event that issues stock to a patient (or POS counter).

    Records the batch the medicine came from and the price charged, and is the
    bridge between the prescription, the inventory ledger and the bill.
    """

    class Status(models.TextChoices):
        DISPENSED = "DISPENSED", "Dispensed"
        RETURNED = "RETURNED", "Returned"
        CANCELLED = "CANCELLED", "Cancelled"

    drug_order = models.ForeignKey(
        DrugOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="dispenses"
    )
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.PROTECT, related_name="dispenses", null=True, blank=True
    )
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.PROTECT, related_name="dispenses"
    )
    location = models.ForeignKey(
        "emr.Location", on_delete=models.PROTECT, related_name="dispenses"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dispensed_by = models.ForeignKey(
        "users.Provider", on_delete=models.SET_NULL, null=True, blank=True, related_name="dispenses"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISPENSED)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient", "-created_at"])]

    def __str__(self):
        return f"Dispense {self.quantity} x {self.product.sku}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price
