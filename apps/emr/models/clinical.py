"""Discrete clinical records: allergies, conditions and diagnoses.

These are first-class FHIR resources (AllergyIntolerance, Condition) and are
modelled explicitly rather than as plain observations so they can be coded,
tracked over time and surfaced on the patient summary.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData


class Allergy(BaseOpenmrsData):
    """A patient allergy/intolerance."""

    class Category(models.TextChoices):
        DRUG = "DRUG", "Drug"
        FOOD = "FOOD", "Food"
        ENVIRONMENT = "ENVIRONMENT", "Environment"
        OTHER = "OTHER", "Other"

    class Severity(models.TextChoices):
        MILD = "MILD", "Mild"
        MODERATE = "MODERATE", "Moderate"
        SEVERE = "SEVERE", "Severe"

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="allergies"
    )
    allergen = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="allergy_records"
    )
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.DRUG)
    severity = models.CharField(max_length=20, choices=Severity.choices, blank=True, default="")
    # Free-text reaction kept for quick entry; coded reactions live in
    # AllergyReaction (OpenMRS allows several coded reactions per allergy).
    reaction = models.CharField(max_length=255, blank=True, default="")
    comment = models.CharField(max_length=255, blank=True, default="")


class AllergyReaction(models.Model):
    """A single coded reaction of an allergy (OpenMRS ``AllergyReaction``).

    An allergy may manifest as several reactions (rash, anaphylaxis, ...), each
    coded to a concept plus optional non-coded detail.
    """

    allergy = models.ForeignKey(
        Allergy, on_delete=models.CASCADE, related_name="reactions"
    )
    reaction = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="allergy_reactions"
    )
    reaction_non_coded = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("allergy", "reaction")

    def __str__(self):
        return f"{self.reaction} ({self.allergy_id})"


class Condition(BaseOpenmrsData):
    """A longitudinal problem-list condition."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        RESOLVED = "RESOLVED", "Resolved"

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="conditions"
    )
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="condition_records"
    )
    clinical_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    onset_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class Diagnosis(BaseOpenmrsData):
    """A diagnosis attached to an encounter (confirmed or provisional)."""

    class Certainty(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROVISIONAL = "PROVISIONAL", "Provisional"

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="diagnoses"
    )
    encounter = models.ForeignKey(
        "emr.Encounter", on_delete=models.CASCADE, related_name="diagnoses", null=True, blank=True
    )
    diagnosis_concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="diagnosis_records"
    )
    certainty = models.CharField(
        max_length=20, choices=Certainty.choices, default=Certainty.CONFIRMED
    )
    rank = models.PositiveSmallIntegerField(
        default=1, help_text="1 = primary diagnosis, 2+ = secondary."
    )

    class Meta:
        verbose_name_plural = "diagnoses"
        ordering = ["rank"]
