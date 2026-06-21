"""Billing reference data: billable services and insurance.

The actual money movement lives in the POS app (Sale/Payment). This app holds
the *catalogue* of chargeable clinical services (consultations, procedures,
bed-days) and the insurance schemes/policies that pay for them, so a POS
service line can be priced consistently and routed to the right payer.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel


class BillableService(BaseOpenmrsMetadata):
    """A chargeable, non-stock service (consultation, procedure, bed-day, ...)."""

    service_code = models.CharField(max_length=64, unique=True, db_index=True)
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True, related_name="billable_services"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.ForeignKey(
        "inventory.TaxRate", on_delete=models.SET_NULL, null=True, blank=True, related_name="services"
    )

    def __str__(self):
        return f"{self.service_code} - {self.name}"


class InsuranceScheme(BaseOpenmrsMetadata):
    """A payer scheme (NHIMA, private insurer, corporate, ...)."""

    payer_name = models.CharField(max_length=160, blank=True, default="")
    coverage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    contact = models.CharField(max_length=160, blank=True, default="")


class PatientInsurance(TimeStampedModel):
    """A patient's enrolment in an insurance scheme."""

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="insurance_policies"
    )
    scheme = models.ForeignKey(
        InsuranceScheme, on_delete=models.PROTECT, related_name="policies"
    )
    policy_number = models.CharField(max_length=120, db_index=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient", "is_active"])]

    def __str__(self):
        return f"{self.scheme.name}: {self.policy_number}"
