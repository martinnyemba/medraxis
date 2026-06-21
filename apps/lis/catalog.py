"""Test-catalogue extensions inspired by FLabs.

Adds the catalogue richness a diagnostic centre needs beyond a flat test list:
methodologies, demographic (age/sex) reference ranges, multi-test profiles, and
formatted report templates. See ``docs/flabs_research.md``.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata


class TestMethod(BaseOpenmrsMetadata):
    """A methodology/instrument-method by which a test is performed.

    e.g. "ELISA", "Chemiluminescence", "Manual microscopy". A test may be
    offered by several methods, each with its own reference ranges.
    """

    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="methods"
    )
    instrument = models.CharField(max_length=120, blank=True, default="")
    is_default = models.BooleanField(default=False)


class ReferenceRange(models.Model):
    """A demographic-specific normal/critical range for a test analyte.

    Diagnostic labs need ranges that vary by **sex** and **age** (and sometimes
    method) -- a single global range is clinically unsafe. The most specific
    matching range wins at flagging time.
    """

    class Sex(models.TextChoices):
        ANY = "A", "Any"
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="reference_ranges"
    )
    analyte = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="reference_ranges",
        null=True, blank=True,
        help_text="Specific analyte for panels; null applies to the test itself.",
    )
    method = models.ForeignKey(
        TestMethod, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reference_ranges",
    )
    sex = models.CharField(max_length=1, choices=Sex.choices, default=Sex.ANY)
    age_min_days = models.IntegerField(null=True, blank=True)
    age_max_days = models.IntegerField(null=True, blank=True)

    low_normal = models.FloatField(null=True, blank=True)
    hi_normal = models.FloatField(null=True, blank=True)
    low_critical = models.FloatField(null=True, blank=True)
    hi_critical = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=50, blank=True, default="")
    text_range = models.CharField(
        max_length=120, blank=True, default="",
        help_text="Display string, e.g. '12 - 16 g/dL' or 'Negative'.",
    )

    class Meta:
        ordering = ["lab_test", "sex", "age_min_days"]
        indexes = [models.Index(fields=["lab_test", "analyte", "sex"])]

    def __str__(self):
        return f"{self.lab_test_id} {self.get_sex_display()} {self.text_range or ''}".strip()

    def matches(self, *, sex=None, age_days=None):
        """True if this range applies to the given patient demographics."""
        if self.sex != self.Sex.ANY and sex and sex != self.sex:
            return False
        if age_days is not None:
            if self.age_min_days is not None and age_days < self.age_min_days:
                return False
            if self.age_max_days is not None and age_days > self.age_max_days:
                return False
        return True

    @property
    def specificity(self):
        """Higher = more specific; used to pick the best-matching range."""
        score = 0
        if self.sex != self.Sex.ANY:
            score += 2
        if self.age_min_days is not None or self.age_max_days is not None:
            score += 1
        return score


class TestProfile(BaseOpenmrsMetadata):
    """A named bundle of tests ordered together (e.g. 'Full Health Checkup').

    Distinct from a panel analyte set: a profile groups whole *tests* (often
    across sections) for convenient ordering and package pricing.
    """

    code = models.CharField(max_length=64, unique=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tests = models.ManyToManyField(
        "lis.LabTest", through="TestProfileMember", related_name="profiles", blank=True
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class TestProfileMember(models.Model):
    """Membership of a test within a profile, with ordering."""

    profile = models.ForeignKey(TestProfile, on_delete=models.CASCADE, related_name="members")
    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="profile_memberships"
    )
    sort_weight = models.FloatField(default=0)

    class Meta:
        ordering = ["sort_weight"]
        unique_together = ("profile", "lab_test")

    def __str__(self):
        return f"{self.lab_test_id} in profile {self.profile_id}"


class ReportTemplate(BaseOpenmrsMetadata):
    """A formatted report layout for a test (methodology, interpretation, notes).

    Drives how a result prints on the patient report -- the templated narrative
    sections diagnostic labs attach to histopathology, serology, etc.
    """

    lab_test = models.ForeignKey(
        "lis.LabTest", on_delete=models.CASCADE, related_name="report_templates"
    )
    methodology_text = models.TextField(blank=True, default="")
    interpretation_template = models.TextField(blank=True, default="")
    footer_notes = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
