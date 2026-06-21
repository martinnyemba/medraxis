"""Visits -- a contiguous period of care that groups encounters.

A visit (OPD attendance, admission, lab walk-in) bundles together all the
encounters that happen during one interaction with the facility.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata
from apps.tenancy.mixins import TenantScopedModel


class VisitType(BaseOpenmrsMetadata):
    """Outpatient, Inpatient, Emergency, Lab Walk-in, Pharmacy Sale, ..."""


class Visit(BaseOpenmrsData, TenantScopedModel):
    """A bounded period during which care/services are provided."""

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.PROTECT, related_name="visits"
    )
    visit_type = models.ForeignKey(
        VisitType, on_delete=models.PROTECT, related_name="visits"
    )
    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="visits"
    )
    started_at = models.DateTimeField(db_index=True)
    stopped_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["patient", "-started_at"])]

    def __str__(self):
        return f"{self.visit_type} for {self.patient} @ {self.started_at:%Y-%m-%d}"

    @property
    def is_active(self):
        return self.stopped_at is None
