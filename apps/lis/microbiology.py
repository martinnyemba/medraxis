"""Microbiology: culture & sensitivity (antibiogram).

Microbiology does not fit a flat numeric result: a culture isolates one or more
**organisms**, and each is tested against a panel of **antibiotics** giving a
Sensitive/Intermediate/Resistant grid. Modelling it first-class (rather than as
text obs) keeps the antibiogram queryable for stewardship and surveillance.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class Organism(BaseOpenmrsMetadata):
    """A micro-organism that can be isolated from a culture."""

    code = models.CharField(max_length=64, blank=True, default="", db_index=True)
    gram_stain = models.CharField(
        max_length=20, blank=True, default="",
        help_text="POSITIVE / NEGATIVE / N-A",
    )


class Antibiotic(BaseOpenmrsMetadata):
    """An antimicrobial agent tested in sensitivity panels."""

    code = models.CharField(max_length=64, blank=True, default="", db_index=True)
    abbreviation = models.CharField(max_length=20, blank=True, default="")


class MicrobiologyResult(BaseOpenmrsData):
    """A culture result for a test order: growth + isolated organism."""

    class Growth(models.TextChoices):
        NO_GROWTH = "NO_GROWTH", "No growth"
        GROWTH = "GROWTH", "Growth"
        MIXED = "MIXED", "Mixed flora"
        CONTAMINATED = "CONTAMINATED", "Contaminated"

    test_order = models.ForeignKey(
        "lis.TestOrder", on_delete=models.CASCADE, related_name="microbiology_results"
    )
    specimen = models.ForeignKey(
        "lis.Specimen", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="microbiology_results",
    )
    growth = models.CharField(max_length=20, choices=Growth.choices, default=Growth.NO_GROWTH)
    organism = models.ForeignKey(
        Organism, on_delete=models.PROTECT, null=True, blank=True, related_name="isolates"
    )
    colony_count = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=20, default="PRELIMINARY",
        help_text="PRELIMINARY / FINAL / AMENDED.",
    )
    comments = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_growth_display()} {self.organism or ''}".strip()


class SensitivityResult(models.Model):
    """One antibiotic's result against an isolated organism (the antibiogram cell)."""

    class Interpretation(models.TextChoices):
        SENSITIVE = "S", "Sensitive"
        INTERMEDIATE = "I", "Intermediate"
        RESISTANT = "R", "Resistant"

    microbiology_result = models.ForeignKey(
        MicrobiologyResult, on_delete=models.CASCADE, related_name="sensitivities"
    )
    antibiotic = models.ForeignKey(
        Antibiotic, on_delete=models.PROTECT, related_name="sensitivities"
    )
    interpretation = models.CharField(max_length=1, choices=Interpretation.choices)
    mic = models.CharField(
        max_length=32, blank=True, default="",
        help_text="Minimum inhibitory concentration, if measured.",
    )

    class Meta:
        unique_together = ("microbiology_result", "antibiotic")
        ordering = ["antibiotic__name"]

    def __str__(self):
        return f"{self.antibiotic_id}: {self.interpretation}"
