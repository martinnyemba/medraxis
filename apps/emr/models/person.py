"""Person demographics -- the base identity shared by patients and providers.

Mirrors OpenMRS ``Person`` and its satellite tables. A ``Patient`` is a
``Person`` with identifiers; a ``Provider`` references a ``Person`` too, so
demographic data is never duplicated.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class Person(BaseOpenmrsData):
    """Core demographics for any human in the system."""

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"
        UNKNOWN = "U", "Unknown"

    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.UNKNOWN)
    birthdate = models.DateField(null=True, blank=True)
    birthdate_estimated = models.BooleanField(default=False)
    dead = models.BooleanField(default=False)
    death_date = models.DateTimeField(null=True, blank=True)
    cause_of_death = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        indexes = [models.Index(fields=["gender", "birthdate"])]

    def __str__(self):
        name = self.preferred_name
        return str(name) if name else f"Person {self.uuid}"

    @property
    def preferred_name(self):
        return self.names.filter(preferred=True).first() or self.names.first()


class PersonName(BaseOpenmrsData):
    """A name for a person (a person may have several over time)."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="names")
    preferred = models.BooleanField(default=False)
    prefix = models.CharField(max_length=50, blank=True, default="")
    given_name = models.CharField(max_length=120, db_index=True)
    middle_name = models.CharField(max_length=120, blank=True, default="")
    family_name = models.CharField(max_length=120, db_index=True)
    family_name_suffix = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["family_name", "given_name"])]

    def __str__(self):
        parts = [self.given_name, self.middle_name, self.family_name]
        return " ".join(p for p in parts if p)


class PersonAddress(BaseOpenmrsData):
    """A postal/physical address for a person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="addresses")
    preferred = models.BooleanField(default=False)
    address1 = models.CharField(max_length=255, blank=True, default="")
    address2 = models.CharField(max_length=255, blank=True, default="")
    city_village = models.CharField(max_length=120, blank=True, default="", db_index=True)
    county_district = models.CharField(max_length=120, blank=True, default="")
    state_province = models.CharField(max_length=120, blank=True, default="")
    country = models.CharField(max_length=120, blank=True, default="")
    postal_code = models.CharField(max_length=32, blank=True, default="")

    def __str__(self):
        return ", ".join(p for p in [self.address1, self.city_village, self.country] if p)


class PersonAttributeType(BaseOpenmrsMetadata):
    """Defines an extensible, typed attribute that can be attached to a person.

    This is OpenMRS's extensibility mechanism for demographics -- e.g.
    "Mother's Name", "Phone Number", "Next of Kin", "Health Insurance ID" --
    without schema changes.
    """

    format = models.CharField(
        max_length=50,
        default="java.lang.String",
        help_text="Logical datatype hint: string, boolean, date, concept, ...",
    )
    searchable = models.BooleanField(default=False)
    sort_weight = models.FloatField(default=0)

    class Meta:
        ordering = ["sort_weight", "name"]


class PersonAttribute(BaseOpenmrsData):
    """A value for a :class:`PersonAttributeType` on a specific person."""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="attributes")
    attribute_type = models.ForeignKey(
        PersonAttributeType, on_delete=models.PROTECT, related_name="values"
    )
    value = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["attribute_type", "value"])]

    def __str__(self):
        return f"{self.attribute_type.name}: {self.value}"
