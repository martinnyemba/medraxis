"""Generic customizable attribute framework (OpenMRS ``AttributeType``/``Attribute``).

OpenMRS lets administrators extend almost any domain entity with typed,
validated *attributes* without schema changes: a ``*AttributeType`` defines a
field (its datatype, and how many values are allowed), and an ``*Attribute``
stores a value for one owner. We provide the two abstract bases here; each owner
(Visit, Location, Provider, Concept, ...) declares a concrete pair that wires in
the owner foreign key.

This mirrors ``org.openmrs.attribute.BaseAttribute`` and
``org.openmrs.attribute.BaseAttributeType``.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class BaseAttributeType(BaseOpenmrsMetadata):
    """Defines an extensible attribute that can be attached to an owner type.

    ``datatype`` names the logical/custom datatype (mirroring OpenMRS's
    ``CustomDatatype`` classname), e.g. ``str``, ``int``, ``date``, ``boolean``,
    ``concept``. ``min_occurs``/``max_occurs`` bound how many values an owner may
    hold (``max_occurs=None`` means unbounded).
    """

    datatype = models.CharField(
        max_length=120,
        default="str",
        help_text="Logical datatype: str, int, float, date, datetime, boolean, concept, ...",
    )
    datatype_config = models.TextField(blank=True, default="")
    preferred_handler = models.CharField(max_length=255, blank=True, default="")
    handler_config = models.TextField(blank=True, default="")
    min_occurs = models.PositiveSmallIntegerField(default=0)
    max_occurs = models.PositiveSmallIntegerField(null=True, blank=True, default=1)

    class Meta:
        abstract = True
        ordering = ["name"]

    @property
    def required(self):
        return bool(self.min_occurs and self.min_occurs > 0)


class BaseAttribute(BaseOpenmrsData):
    """Stores one value for a ``*AttributeType`` on a specific owner.

    The value is held as ``value_reference`` (text) -- a serialized form whose
    interpretation is governed by the attribute type's datatype, exactly as
    OpenMRS stores attribute values as a value-reference string.
    """

    value_reference = models.TextField(blank=True, default="")

    class Meta:
        abstract = True

    def __str__(self):
        return self.value_reference
