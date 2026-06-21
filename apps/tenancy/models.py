"""Multi-tenancy: an Organization (facility/tenant) owns scoped data.

Medraxis uses **row-level** multi-tenancy: tenant-scoped records carry an
``organization`` foreign key, and queries are automatically filtered to the
current tenant resolved per request. This keeps a single database/schema while
isolating each clinic, lab or pharmacy group's data.

A user may belong to several organizations through :class:`Membership` (for
shared services or head-office staff); the active organization for a request is
chosen from a header or the user's default membership.
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Organization(TimeStampedModel):
    """A tenant: a facility or facility group that owns its data."""

    class OrgType(models.TextChoices):
        CLINIC = "CLINIC", "Clinic"
        HOSPITAL = "HOSPITAL", "Hospital"
        LABORATORY = "LABORATORY", "Diagnostic / Laboratory"
        PHARMACY = "PHARMACY", "Pharmacy"
        GROUP = "GROUP", "Facility group"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    org_type = models.CharField(max_length=20, choices=OrgType.choices, default=OrgType.CLINIC)
    is_active = models.BooleanField(default=True)

    # Light-weight per-tenant configuration / branding.
    legal_name = models.CharField(max_length=200, blank=True, default="")
    tax_identifier = models.CharField(max_length=64, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    currency = models.CharField(max_length=8, default="USD")
    timezone = models.CharField(max_length=64, default="UTC")
    logo = models.ImageField(upload_to="org_logos/", null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(TimeStampedModel):
    """Associates a user with an organization (with an organization-scoped role)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    is_default = models.BooleanField(
        default=False, help_text="The organization selected by default at login."
    )
    is_admin = models.BooleanField(
        default=False, help_text="Organization-level administrator."
    )

    class Meta:
        unique_together = ("user", "organization")
        indexes = [models.Index(fields=["user", "is_default"])]

    def __str__(self):
        return f"{self.user} @ {self.organization}"
