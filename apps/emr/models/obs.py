"""Observations (Obs) -- the universal clinical/lab data point.

A single ``Obs`` row records one answer to one question (concept) for one
person at one time. The question's datatype decides which ``value_*`` column
is used. Observations can be grouped (``obs_group``) to represent structured
forms or lab panels. This one flexible table stores vitals, diagnoses,
symptoms, lab results and more -- the core of the EAV-style OpenMRS model.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData


class Obs(BaseOpenmrsData):
    """One observed value for one concept."""

    person = models.ForeignKey(
        "emr.Person", on_delete=models.PROTECT, related_name="observations"
    )
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="observations"
    )
    encounter = models.ForeignKey(
        "emr.Encounter",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="observations",
    )
    order = models.ForeignKey(
        "emr.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
        help_text="The order that this observation fulfils (e.g. a lab result).",
    )
    obs_datetime = models.DateTimeField(db_index=True)
    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    obs_group = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="group_members",
        help_text="Parent grouping observation (for panels / structured forms).",
    )

    # Polymorphic value columns -- exactly one is populated per datatype.
    value_coded = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, null=True, blank=True, related_name="coded_values"
    )
    value_numeric = models.FloatField(null=True, blank=True)
    value_text = models.TextField(blank=True, default="")
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_complex = models.CharField(
        max_length=255, blank=True, default="", help_text="Pointer to complex data (image, file)."
    )

    # Result interpretation (used heavily by the LIS for flags H/L/Critical).
    class Interpretation(models.TextChoices):
        NORMAL = "N", "Normal"
        HIGH = "H", "High"
        LOW = "L", "Low"
        CRITICAL_HIGH = "HH", "Critical high"
        CRITICAL_LOW = "LL", "Critical low"
        ABNORMAL = "A", "Abnormal"

    interpretation = models.CharField(
        max_length=2, choices=Interpretation.choices, blank=True, default=""
    )
    comments = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        default="FINAL",
        help_text="PRELIMINARY / FINAL / AMENDED (FHIR observation status).",
    )

    class Meta:
        ordering = ["-obs_datetime"]
        indexes = [
            models.Index(fields=["person", "concept", "-obs_datetime"]),
            models.Index(fields=["encounter"]),
        ]

    def __str__(self):
        return f"Obs {self.concept_id}={self.display_value} ({self.person_id})"

    @property
    def display_value(self):
        if self.value_coded_id:
            return self.value_coded.name
        if self.value_numeric is not None:
            return self.value_numeric
        if self.value_boolean is not None:
            return self.value_boolean
        if self.value_datetime is not None:
            return self.value_datetime
        return self.value_text
