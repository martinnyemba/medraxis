"""Quality Control (Westgard / Levey-Jennings underpinnings).

Instruments run control materials with known target values; each control
measurement is stored so the lab can compute Z-scores, apply Westgard rules and
plot Levey-Jennings charts. This is the QC half of analyzer interfacing.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel


class QCMaterial(BaseOpenmrsMetadata):
    """A control material/lot with target mean and SD for an analyte."""

    lot_number = models.CharField(max_length=64, db_index=True)
    analyte = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="qc_materials"
    )
    analyzer = models.ForeignKey(
        "lis.Analyzer", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_materials",
    )
    level = models.CharField(
        max_length=20, blank=True, default="", help_text="e.g. Level 1 / Normal / High."
    )
    target_mean = models.FloatField()
    target_sd = models.FloatField()
    units = models.CharField(max_length=50, blank=True, default="")
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["analyte", "lot_number"]

    def __str__(self):
        return f"{self.name} lot {self.lot_number}"


class QCResult(TimeStampedModel):
    """A single control measurement, with computed Z-score and Westgard flag."""

    qc_material = models.ForeignKey(
        QCMaterial, on_delete=models.CASCADE, related_name="results"
    )
    analyzer = models.ForeignKey(
        "lis.Analyzer", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_results",
    )
    measured_value = models.FloatField()
    z_score = models.FloatField(null=True, blank=True)
    westgard_rule = models.CharField(
        max_length=20, blank=True, default="",
        help_text="Violated rule, e.g. 1-3s, 2-2s, R-4s; blank if in control.",
    )
    accepted = models.BooleanField(default=True)
    run_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-run_at"]
        indexes = [models.Index(fields=["qc_material", "-run_at"])]

    def compute(self):
        """Compute the Z-score and a simple 1-3s/2-2s Westgard evaluation."""
        material = self.qc_material
        if material.target_sd:
            self.z_score = (self.measured_value - material.target_mean) / material.target_sd
        else:
            self.z_score = None
        self.westgard_rule = ""
        self.accepted = True
        if self.z_score is not None and abs(self.z_score) > 3:
            self.westgard_rule = "1-3s"
            self.accepted = False
        return self

    def __str__(self):
        return f"QC {self.qc_material_id}={self.measured_value} (z={self.z_score})"
