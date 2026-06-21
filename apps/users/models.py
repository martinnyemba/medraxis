"""User, Role, Privilege and Provider models.

Authentication & authorization follow the OpenMRS security model:

* ``Privilege`` -- a single fine-grained capability ("Add Patients",
  "View Observations", "Manage Lab Results", ...).
* ``Role``      -- a named bundle of privileges that can *inherit* other roles
  (e.g. "Clinician" inherits "Data Entry").
* ``User``      -- a login account that holds one or more roles.
* ``Provider``  -- the clinical identity (doctor, nurse, lab tech) that
  authors encounters, orders and results. A provider is linked to an EMR
  ``Person`` and optionally to a login ``User``.

Note on the User<->Person link: to keep the ``users`` and ``emr`` apps free of
circular migration dependencies, the demographic ``Person`` record lives in
``emr`` and is referenced from ``Provider`` (and from ``Patient``), not from
``User``. ``User`` carries only the minimal account-level name fields.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.attributes import BaseAttribute, BaseAttributeType
from apps.core.models import BaseOpenmrsMetadata, TimeStampedModel


class Privilege(TimeStampedModel):
    """A single, fine-grained capability checked at the application layer."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Role(TimeStampedModel):
    """A named bundle of privileges, optionally inheriting other roles."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    privileges = models.ManyToManyField(Privilege, related_name="roles", blank=True)
    inherited_roles = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="child_roles",
        blank=True,
        help_text="Roles whose privileges are also granted by this role.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def all_privileges(self, _seen=None):
        """Return this role's privileges plus those of inherited roles."""
        _seen = _seen or set()
        if self.pk in _seen:
            return set()
        _seen.add(self.pk)
        privileges = set(self.privileges.all())
        for parent in self.inherited_roles.all():
            privileges |= parent.all_privileges(_seen)
        return privileges


class User(AbstractUser):
    """Custom login account.

    Extends Django's ``AbstractUser`` (username, email, password, groups,
    permissions) with OpenMRS-style roles and a system-account flag.
    """

    email = models.EmailField("email address", unique=True)
    roles = models.ManyToManyField(Role, related_name="users", blank=True)
    is_system_account = models.BooleanField(
        default=False,
        help_text="Non-human account used for integrations / scheduled jobs.",
    )
    force_password_change = models.BooleanField(default=False)
    phone = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        ordering = ["username"]

    def has_privilege(self, privilege_name):
        """True if any of the user's roles grant ``privilege_name``.

        Superusers implicitly hold every privilege.
        """
        if self.is_superuser:
            return True
        for role in self.roles.all():
            if any(p.name == privilege_name for p in role.all_privileges()):
                return True
        return False

    def privilege_names(self):
        names = set()
        for role in self.roles.all():
            names |= {p.name for p in role.all_privileges()}
        return names


class Provider(BaseOpenmrsMetadata):
    """A clinician or operational actor who authors clinical/lab records.

    Mirrors ``org.openmrs.Provider``: linked to a ``Person`` for demographics
    and optionally to a login ``User``.
    """

    identifier = models.CharField(
        max_length=64,
        unique=True,
        help_text="Provider/registration number (e.g. medical council number).",
    )
    person = models.ForeignKey(
        "emr.Person",
        on_delete=models.PROTECT,
        related_name="providers",
        null=True,
        blank=True,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="provider",
        null=True,
        blank=True,
    )
    provider_role = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Doctor, Nurse, Lab Technologist, Pharmacist, Cashier, ...",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.identifier})"


class ProviderAttributeType(BaseAttributeType):
    """Defines a custom attribute attachable to a Provider.

    e.g. 'Specialty', 'License expiry', 'Council number type' -- the OpenMRS
    customizable-attribute pattern applied to providers.
    """


class ProviderAttribute(BaseAttribute):
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="attributes"
    )
    attribute_type = models.ForeignKey(
        ProviderAttributeType, on_delete=models.PROTECT, related_name="values"
    )
