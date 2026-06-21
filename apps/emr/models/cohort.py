"""Cohorts -- named, membership-tracked groups of patients (OpenMRS ``Cohort``).

Cohorts underpin reporting and program management: a static or query-defined set
of patients (e.g. "ART patients due for review"). Memberships are time-bounded
so a patient's presence in a cohort is auditable over time.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class Cohort(BaseOpenmrsMetadata):
    """A named group of patients."""

    class Meta:
        ordering = ["name"]


class CohortMembership(BaseOpenmrsData):
    """A patient's time-bounded membership in a cohort."""

    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="memberships")
    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="cohort_memberships"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["cohort", "patient"])]

    def __str__(self):
        return f"{self.patient_id} in {self.cohort_id}"
