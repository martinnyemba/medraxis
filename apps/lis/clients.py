"""Multi-branch & B2B models inspired by FLabs.

A diagnostic centre serves walk-ins, referring doctors and B2B clients
(hospitals, corporates, camps), collects samples at many centres (incl. home
collection), and outsources some tests to external reference labs. These models
capture that commercial/operational layer. See ``docs/flabs_research.md``.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel


class ReferringDoctor(BaseOpenmrsMetadata):
    """A doctor who refers patients to the lab (with optional commission).

    Distinct from ``users.Provider`` (internal staff): a referrer is an external
    party tracked for reporting, marketing and commission/settlement.
    """

    code = models.CharField(max_length=64, unique=True, db_index=True)
    specialty = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    hospital = models.CharField(max_length=160, blank=True, default="")
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Client(BaseOpenmrsMetadata):
    """A B2B account that sends work to the lab (hospital, corporate, camp, branch)."""

    class ClientType(models.TextChoices):
        HOSPITAL = "HOSPITAL", "Hospital"
        CORPORATE = "CORPORATE", "Corporate"
        COLLECTION_CENTER = "COLLECTION_CENTER", "Collection center"
        CAMP = "CAMP", "Health camp"
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=64, unique=True, db_index=True)
    client_type = models.CharField(
        max_length=20, choices=ClientType.choices, default=ClientType.HOSPITAL
    )
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_credit = models.BooleanField(default=False, help_text="Billed on account vs prepaid.")

    def __str__(self):
        return f"{self.name} ({self.code})"


class PriceList(BaseOpenmrsMetadata):
    """A negotiated rate card, optionally tied to a specific B2B client."""

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, blank=True, related_name="price_lists"
    )
    is_default = models.BooleanField(default=False)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)


class PriceListItem(models.Model):
    """A test's price within a price list."""

    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name="items")
    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="price_list_items"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("price_list", "lab_test")

    def __str__(self):
        return f"{self.lab_test_id} @ {self.price}"


class CollectionCenter(BaseOpenmrsMetadata):
    """A sample collection point (branch) that feeds a processing lab.

    A branch *within* a tenant brand. Links to an EMR ``Location`` for the
    physical/organisational node and to the processing lab it routes to.
    """

    code = models.CharField(max_length=64, unique=True, db_index=True)
    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="collection_centers",
    )
    processing_lab = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="served_collection_centers",
    )
    phone = models.CharField(max_length=32, blank=True, default="")
    is_home_collection = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"


class CollectionAppointment(TimeStampedModel):
    """A scheduled sample collection -- in-centre or home collection."""

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        EN_ROUTE = "EN_ROUTE", "Phlebotomist en route"
        COLLECTED = "COLLECTED", "Collected"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No show"

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="collection_appointments"
    )
    collection_center = models.ForeignKey(
        CollectionCenter, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="appointments",
    )
    scheduled_for = models.DateTimeField(db_index=True)
    is_home_collection = models.BooleanField(default=False)
    address = models.TextField(blank=True, default="")
    phlebotomist = models.ForeignKey(
        "users.Provider", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="collection_appointments",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-scheduled_for"]

    def __str__(self):
        return f"Appointment {self.patient_id} @ {self.scheduled_for:%Y-%m-%d %H:%M}"


class ReferenceLab(BaseOpenmrsMetadata):
    """An external laboratory to which tests are outsourced."""

    code = models.CharField(max_length=64, unique=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    default_tat_hours = models.PositiveIntegerField(default=72)

    def __str__(self):
        return f"{self.name} ({self.code})"
