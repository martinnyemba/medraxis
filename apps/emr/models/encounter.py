"""Encounters -- a single clinical interaction within a visit.

An encounter (consultation, triage, lab specimen collection, drug dispense)
is the container that observations and orders attach to, and records *who*
(providers) did *what* (type) *where* (location) and *when*.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata
from apps.tenancy.mixins import TenantScopedModel


class EncounterType(BaseOpenmrsMetadata):
    """Consultation, Triage, Lab, Dispensing, Vitals, Admission, ..."""


class EncounterRole(BaseOpenmrsMetadata):
    """The capacity in which a provider participates (e.g. Consulting Clinician)."""


class Encounter(BaseOpenmrsData, TenantScopedModel):
    """A clinical interaction; the parent of observations and orders."""

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.PROTECT, related_name="encounters"
    )
    encounter_type = models.ForeignKey(
        EncounterType, on_delete=models.PROTECT, related_name="encounters"
    )
    visit = models.ForeignKey(
        "emr.Visit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encounters",
    )
    location = models.ForeignKey(
        "emr.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encounters",
    )
    encounter_datetime = models.DateTimeField(db_index=True)
    providers = models.ManyToManyField(
        "users.Provider", through="EncounterProvider", related_name="encounters"
    )
    form_reference = models.CharField(
        max_length=120, blank=True, default="", help_text="Optional originating form id."
    )

    class Meta:
        ordering = ["-encounter_datetime"]
        indexes = [models.Index(fields=["patient", "-encounter_datetime"])]

    def __str__(self):
        return f"{self.encounter_type} for {self.patient} @ {self.encounter_datetime:%Y-%m-%d}"


class EncounterProvider(BaseOpenmrsData):
    """Associates a provider with an encounter in a specific role."""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="encounter_providers"
    )
    provider = models.ForeignKey(
        "users.Provider", on_delete=models.PROTECT, related_name="encounter_providers"
    )
    encounter_role = models.ForeignKey(
        EncounterRole, on_delete=models.PROTECT, related_name="encounter_providers"
    )

    class Meta:
        unique_together = ("encounter", "provider", "encounter_role")
