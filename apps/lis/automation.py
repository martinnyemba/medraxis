"""Result auto-verification & reflex rules (the implementable core of "AI").

Modern lab "AI automation" is, underneath, a transparent rule engine that
releases results needing no human eyes and holds the rest. A rule governs a test
and decides, per result, whether it can auto-verify -- gating on in-range values,
absence of critical flags, and a delta check against the patient's previous
result. Reflex rules can auto-order a follow-up test on abnormality.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata


class AutoVerificationRule(BaseOpenmrsMetadata):
    """Configurable auto-verification policy for a test.

    The rule is intentionally explicit and auditable; an ML scorer can later be
    plugged in behind the same evaluation service without changing callers.
    """

    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="auto_verification_rules"
    )
    enabled = models.BooleanField(default=True)
    require_in_range = models.BooleanField(
        default=True, help_text="Only auto-verify results within the reference range."
    )
    block_on_critical = models.BooleanField(
        default=True, help_text="Never auto-verify a critical/panic result."
    )
    delta_check_percent = models.FloatField(
        null=True, blank=True,
        help_text="Hold if the result differs from the patient's previous value "
                  "by more than this %.",
    )
    # Reflex testing: when abnormal, auto-order another test.
    reflex_on_abnormal = models.ForeignKey(
        "lis.LabTest", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reflex_triggers",
        help_text="Test to auto-order when this result is abnormal.",
    )

    class Meta:
        ordering = ["lab_test"]

    def __str__(self):
        return f"Auto-verify rule for {self.lab_test_id}"
