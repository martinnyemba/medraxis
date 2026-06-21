"""Patient and patient identifiers.

A ``Patient`` *is a* ``Person`` (OpenMRS uses class inheritance; here we use a
one-to-one extension to keep demographics in one place). Patients are found in
practice by their identifiers (hospital number, national ID, NHIMA, ...),
each of which is defined by a :class:`PatientIdentifierType`.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata
from apps.tenancy.mixins import TenantScopedModel


class PatientIdentifierType(BaseOpenmrsMetadata):
    """Defines a class of patient identifier and its validation rules."""

    class Uniqueness(models.TextChoices):
        UNIQUE = "UNIQUE", "Unique"
        NON_UNIQUE = "NON_UNIQUE", "Non-unique"
        LOCATION = "LOCATION", "Unique per location"

    format_regex = models.CharField(
        max_length=255, blank=True, default="", help_text="Optional validation regex."
    )
    format_description = models.CharField(max_length=255, blank=True, default="")
    required = models.BooleanField(default=False)
    check_digit_algorithm = models.CharField(max_length=120, blank=True, default="")
    uniqueness_behavior = models.CharField(
        max_length=20, choices=Uniqueness.choices, default=Uniqueness.UNIQUE
    )


class Patient(BaseOpenmrsData, TenantScopedModel):
    """A person who receives care -- the central EMR record."""

    person = models.OneToOneField(
        "emr.Person", on_delete=models.PROTECT, related_name="patient"
    )
    # Denormalised convenience flag kept in sync with PatientProgram, etc.
    allergy_status = models.CharField(
        max_length=20,
        default="Unknown",
        help_text="Unknown / No Known Allergies / See List",
    )

    def __str__(self):
        return f"Patient {self.person.preferred_name or self.uuid}"

    @property
    def preferred_identifier(self):
        return self.identifiers.filter(preferred=True).first() or self.identifiers.first()


class PatientIdentifier(BaseOpenmrsData):
    """An identifier value assigned to a patient."""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="identifiers"
    )
    identifier_type = models.ForeignKey(
        PatientIdentifierType, on_delete=models.PROTECT, related_name="identifiers"
    )
    identifier = models.CharField(max_length=120, db_index=True)
    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    preferred = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["identifier_type", "identifier"])]

    def __str__(self):
        return f"{self.identifier_type.name}: {self.identifier}"
