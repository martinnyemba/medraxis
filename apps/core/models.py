"""Core abstract models and platform-wide concrete models.

The abstract base classes here are a direct Django translation of the OpenMRS
domain object hierarchy:

* ``BaseOpenmrsObject``   -> a globally-unique, FHIR-friendly ``uuid``.
* ``BaseOpenmrsData``     -> auditable + *voidable* transactional data
                              (Patient, Encounter, Obs, Order, Visit, ...).
* ``BaseOpenmrsMetadata`` -> auditable + *retireable* reference/metadata
                              (ConceptClass, EncounterType, Location, ...).

Every domain app extends these so that auditing, soft deletion, and FHIR
identity behave consistently across EMR, LIS, pharmacy, inventory and POS.
"""
import uuid as uuid_lib

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.managers import RetireableManager, VoidableManager


class TimeStampedModel(models.Model):
    """Simple created/updated timestamps for non-OpenMRS-style models."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseOpenmrsObject(models.Model):
    """Root of the domain hierarchy: every object carries a stable UUID.

    The UUID is the natural key for FHIR resource identity and for
    cross-system references (e.g. a LIS result pointing back at an EMR order).
    """

    uuid = models.UUIDField(
        default=uuid_lib.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Globally unique, FHIR-friendly identifier.",
    )

    class Meta:
        abstract = True


class BaseOpenmrsData(BaseOpenmrsObject):
    """Auditable, *voidable* transactional data.

    Mirrors ``org.openmrs.BaseOpenmrsData``. Records are never physically
    deleted in normal operation; they are voided with an audit trail.
    """

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        editable=False,
    )
    changed_at = models.DateTimeField(null=True, blank=True, editable=False)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        editable=False,
    )
    voided = models.BooleanField(default=False, db_index=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )
    void_reason = models.CharField(max_length=255, blank=True, default="")

    # ``objects`` hides voided rows; ``all_objects`` exposes everything.
    objects = VoidableManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["id"]

    def save(self, *args, **kwargs):
        """Stamp creator / changed_by from the current request user."""
        from apps.core.middleware.audit_user import get_current_user

        user = get_current_user()
        if self._state.adding:
            if user and getattr(user, "is_authenticated", False) and self.creator_id is None:
                self.creator = user
        else:
            self.changed_at = timezone.now()
            if user and getattr(user, "is_authenticated", False):
                self.changed_by = user
        super().save(*args, **kwargs)

    def void(self, user=None, reason=""):
        """Soft-delete this record with an audit trail."""
        self.voided = True
        self.voided_at = timezone.now()
        self.voided_by = user
        self.void_reason = reason
        self.save(update_fields=["voided", "voided_at", "voided_by", "void_reason"])

    def unvoid(self):
        """Restore a previously voided record."""
        self.voided = False
        self.voided_at = None
        self.voided_by = None
        self.void_reason = ""
        self.save(update_fields=["voided", "voided_at", "voided_by", "void_reason"])


class BaseOpenmrsMetadata(BaseOpenmrsObject):
    """Auditable, *retireable* reference/metadata.

    Mirrors ``org.openmrs.BaseOpenmrsMetadata``. Used for configuration and
    dictionary-style records that are retired rather than deleted.
    """

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        editable=False,
    )
    changed_at = models.DateTimeField(null=True, blank=True, editable=False)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        editable=False,
    )
    retired = models.BooleanField(default=False, db_index=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    retired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )
    retire_reason = models.CharField(max_length=255, blank=True, default="")

    objects = RetireableManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from apps.core.middleware.audit_user import get_current_user

        user = get_current_user()
        if self._state.adding:
            if user and getattr(user, "is_authenticated", False) and self.creator_id is None:
                self.creator = user
        else:
            self.changed_at = timezone.now()
            if user and getattr(user, "is_authenticated", False):
                self.changed_by = user
        super().save(*args, **kwargs)

    def retire(self, user=None, reason=""):
        self.retired = True
        self.retired_at = timezone.now()
        self.retired_by = user
        self.retire_reason = reason
        self.save(update_fields=["retired", "retired_at", "retired_by", "retire_reason"])

    def unretire(self):
        self.retired = False
        self.retired_at = None
        self.retired_by = None
        self.retire_reason = ""
        self.save(update_fields=["retired", "retired_at", "retired_by", "retire_reason"])


# ---------------------------------------------------------------------------
# Concrete platform-wide models
# ---------------------------------------------------------------------------
class GlobalProperty(TimeStampedModel):
    """Runtime-configurable settings, modelled on OpenMRS global properties.

    Lets administrators tune behaviour (identifier formats, default locale,
    tax rates, etc.) without code changes or redeployment.
    """

    property = models.CharField(max_length=255, unique=True)
    property_value = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    datatype = models.CharField(
        max_length=50,
        default="string",
        help_text="Logical type hint: string, int, boolean, json, ...",
    )

    class Meta:
        verbose_name = "global property"
        verbose_name_plural = "global properties"
        ordering = ["property"]

    def __str__(self):
        return self.property


class AuditLog(models.Model):
    """Immutable audit trail for sensitive actions across the platform.

    Written by signals/services rather than edited directly. Captures who did
    what, to which record, and from where — required for healthcare
    compliance.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        VOID = "void", "Void"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        ACCESS = "access", "Access"
        EXPORT = "export", "Export"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    model_name = models.CharField(max_length=120, db_index=True)
    object_pk = models.CharField(max_length=64, blank=True, default="", db_index=True)
    object_uuid = models.UUIDField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "object_pk"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name}#{self.object_pk} by {self.actor_id}"
