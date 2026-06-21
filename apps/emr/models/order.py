"""Orders -- the request/fulfilment backbone shared across the platform.

The base ``Order`` is deliberately generic (OpenMRS does the same). The LIS
extends it with ``TestOrder`` and the pharmacy with ``DrugOrder`` via
multi-table inheritance, so lab requests and prescriptions share one
order lifecycle, numbering scheme and fulfilment status -- and one place to
query "everything ordered for this patient".
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata
from apps.tenancy.mixins import TenantScopedModel


class OrderType(BaseOpenmrsMetadata):
    """Test Order, Drug Order, Radiology Order, Referral, ..."""

    java_class_name = models.CharField(
        max_length=120, blank=True, default="", help_text="Backing model, for routing."
    )


class OrderFrequency(BaseOpenmrsMetadata):
    """A coded administration frequency (OpenMRS ``OrderFrequency``).

    Wraps a concept (e.g. "Twice daily") with a machine-usable
    ``frequency_per_day`` so drug orders carry structured, codeable frequency
    rather than free text.
    """

    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="order_frequencies"
    )
    frequency_per_day = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "order frequencies"
        ordering = ["name"]


class CareSetting(BaseOpenmrsMetadata):
    """Outpatient vs Inpatient context for an order."""

    class CareSettingType(models.TextChoices):
        OUTPATIENT = "OUTPATIENT", "Outpatient"
        INPATIENT = "INPATIENT", "Inpatient"

    care_setting_type = models.CharField(
        max_length=20, choices=CareSettingType.choices, default=CareSettingType.OUTPATIENT
    )


class Order(BaseOpenmrsData, TenantScopedModel):
    """A request for a service or product for a patient."""

    class Action(models.TextChoices):
        NEW = "NEW", "New"
        REVISE = "REVISE", "Revise"
        DISCONTINUE = "DISCONTINUE", "Discontinue"
        RENEW = "RENEW", "Renew"

    class Urgency(models.TextChoices):
        ROUTINE = "ROUTINE", "Routine"
        STAT = "STAT", "Stat"
        ON_SCHEDULED_DATE = "ON_SCHEDULED_DATE", "On scheduled date"

    class FulfillerStatus(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        EXCEPTION = "EXCEPTION", "Exception"
        ON_HOLD = "ON_HOLD", "On hold"
        DECLINED = "DECLINED", "Declined"
        COMPLETED = "COMPLETED", "Completed"

    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    order_type = models.ForeignKey(OrderType, on_delete=models.PROTECT, related_name="orders")
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="orders"
    )
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.PROTECT, related_name="orders"
    )
    encounter = models.ForeignKey(
        "emr.Encounter", on_delete=models.PROTECT, related_name="orders", null=True, blank=True
    )
    orderer = models.ForeignKey(
        "users.Provider", on_delete=models.PROTECT, related_name="orders", null=True, blank=True
    )
    care_setting = models.ForeignKey(
        CareSetting, on_delete=models.PROTECT, related_name="orders", null=True, blank=True
    )

    order_action = models.CharField(max_length=20, choices=Action.choices, default=Action.NEW)
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.ROUTINE)
    instructions = models.TextField(blank=True, default="")

    date_activated = models.DateTimeField(db_index=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    date_stopped = models.DateTimeField(null=True, blank=True)
    auto_expire_date = models.DateTimeField(null=True, blank=True)

    fulfiller_status = models.CharField(
        max_length=20, choices=FulfillerStatus.choices, blank=True, default=""
    )
    fulfiller_comment = models.CharField(max_length=255, blank=True, default="")
    previous_order = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="revisions"
    )
    order_group = models.ForeignKey(
        "emr.OrderGroup", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="orders",
    )

    class Meta:
        ordering = ["-date_activated"]
        indexes = [
            models.Index(fields=["patient", "-date_activated"]),
            models.Index(fields=["fulfiller_status"]),
        ]

    def __str__(self):
        return f"{self.order_number} ({self.concept})"

    @property
    def is_active(self):
        return self.date_stopped is None and self.order_action != self.Action.DISCONTINUE


class OrderSet(BaseOpenmrsMetadata):
    """A reusable, orderable bundle of items (OpenMRS ``OrderSet``).

    e.g. an "Antenatal first visit" set or a "Sepsis bundle" -- a protocol the
    clinician can order as one unit.
    """

    operator = models.CharField(
        max_length=20, default="ALL",
        help_text="ALL / ANY / ONE -- how members are selected when ordering.",
    )
    category = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="order_sets",
    )


class OrderSetMember(BaseOpenmrsData):
    """A single orderable within an order set."""

    order_set = models.ForeignKey(
        OrderSet, on_delete=models.CASCADE, related_name="members"
    )
    order_type = models.ForeignKey(OrderType, on_delete=models.PROTECT, related_name="+")
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="order_set_members"
    )
    sort_weight = models.FloatField(default=0)

    class Meta:
        ordering = ["sort_weight"]


class OrderGroup(BaseOpenmrsData):
    """Groups orders that were placed together (OpenMRS ``OrderGroup``).

    Links a set of concrete orders back to the encounter and, optionally, the
    order set they were generated from -- so "the orders made on this form" stay
    together.
    """

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="order_groups"
    )
    encounter = models.ForeignKey(
        "emr.Encounter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="order_groups",
    )
    order_set = models.ForeignKey(
        OrderSet, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_groups"
    )

    def __str__(self):
        return f"OrderGroup #{self.pk} for {self.patient_id}"
