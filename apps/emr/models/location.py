"""Locations -- the physical/organisational hierarchy.

A single OpenMRS-style ``Location`` tree models facilities, departments,
wards, rooms, lab benches, pharmacy counters and POS terminals/stores. Tags
let a location play multiple roles (e.g. both "Login Location" and
"Dispensing Location").
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata
from apps.tenancy.mixins import TenantScopedModel


class LocationTag(BaseOpenmrsMetadata):
    """A role label that can be applied to locations."""


class Location(BaseOpenmrsMetadata, TenantScopedModel):
    """A node in the location hierarchy (facility -> ward -> room ...)."""

    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    address1 = models.CharField(max_length=255, blank=True, default="")
    city_village = models.CharField(max_length=120, blank=True, default="")
    state_province = models.CharField(max_length=120, blank=True, default="")
    country = models.CharField(max_length=120, blank=True, default="")
    postal_code = models.CharField(max_length=32, blank=True, default="")
    tags = models.ManyToManyField(LocationTag, related_name="locations", blank=True)

    class Meta:
        indexes = [models.Index(fields=["parent"])]

    def has_tag(self, tag_name):
        return self.tags.filter(name=tag_name).exists()
