"""Drug formulations in the concept dictionary (OpenMRS ``Drug``).

In OpenMRS a ``Drug`` is the specific *formulation* of a drug ``Concept`` --
e.g. the concept "Amoxicillin" has drugs "Amoxicillin 250mg capsule" and
"Amoxicillin 500mg tablet". Clinical orders (``DrugOrder``) reference a ``Drug``;
the inventory ``Product`` is the sellable/stockable counterpart. Keeping the
clinical drug separate from the stock item is what lets one formulation map to
several suppliers' products.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata


class Drug(BaseOpenmrsMetadata):
    """A specific formulation of a drug concept."""

    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="drugs",
        help_text="The drug concept this is a formulation of.",
    )
    combination = models.BooleanField(default=False)
    dosage_form = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="dosage_form_drugs",
        help_text="Tablet, Capsule, Syrup, Injection, ... (a coded concept).",
    )
    strength = models.CharField(max_length=120, blank=True, default="")
    maximum_daily_dose = models.FloatField(null=True, blank=True)
    minimum_daily_dose = models.FloatField(null=True, blank=True)
    dose_units = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="dose_unit_drugs",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DrugIngredient(models.Model):
    """An ingredient (with optional strength) of a combination drug."""

    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="ingredient_of_drugs"
    )
    strength = models.FloatField(null=True, blank=True)
    units = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ingredient_unit_of",
    )

    class Meta:
        unique_together = ("drug", "ingredient")

    def __str__(self):
        return f"{self.ingredient} in {self.drug}"
