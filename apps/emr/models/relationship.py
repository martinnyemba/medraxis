"""Person-to-person relationships (OpenMRS ``Relationship``/``RelationshipType``).

Models directed relationships between two people -- e.g. Parent/Child,
Guardian/Dependant, Doctor/Patient, Caregiver/Patient. The relationship type
names both sides (``a_is_to_b`` and ``b_is_to_a``) so the same row reads
correctly from either person's perspective.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class RelationshipType(BaseOpenmrsMetadata):
    """A bidirectional relationship label, e.g. Parent <-> Child."""

    a_is_to_b = models.CharField(
        max_length=120, help_text="How person A relates to person B (e.g. 'Parent')."
    )
    b_is_to_a = models.CharField(
        max_length=120, help_text="How person B relates to person A (e.g. 'Child')."
    )
    preferred = models.BooleanField(default=False)
    weight = models.IntegerField(default=0)

    class Meta:
        ordering = ["weight", "name"]

    def __str__(self):
        return f"{self.a_is_to_b}/{self.b_is_to_a}"


class Relationship(BaseOpenmrsData):
    """A relationship instance between two persons of a given type."""

    person_a = models.ForeignKey(
        "emr.Person", on_delete=models.CASCADE, related_name="relationships_as_a"
    )
    person_b = models.ForeignKey(
        "emr.Person", on_delete=models.CASCADE, related_name="relationships_as_b"
    )
    relationship_type = models.ForeignKey(
        RelationshipType, on_delete=models.PROTECT, related_name="relationships"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["person_a", "relationship_type"]),
            models.Index(fields=["person_b", "relationship_type"]),
        ]

    def __str__(self):
        return f"{self.person_a_id} {self.relationship_type.a_is_to_b} {self.person_b_id}"
