"""Form metadata (OpenMRS ``Form``/``FormField``/``Field``/``FieldType``).

OpenMRS forms drive structured data entry: a ``Form`` is composed of
``FormField``s (with ordering and hierarchy), each pointing at a reusable
``Field``. A field is usually backed by a ``Concept`` (so the data captured
flows into ``Obs`` against that concept), and is categorised by a ``FieldType``.
``FormResource`` attaches arbitrary resources (e.g. an HTML Form Entry schema)
to a form.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class FieldType(BaseOpenmrsMetadata):
    """Categorises a field: Concept, Database element, Section, Set of coded, ..."""

    is_set = models.BooleanField(default=False)


class Field(BaseOpenmrsMetadata):
    """A reusable data-entry field, usually backed by a concept."""

    field_type = models.ForeignKey(
        FieldType, on_delete=models.PROTECT, related_name="fields", null=True, blank=True
    )
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.SET_NULL, null=True, blank=True, related_name="fields"
    )
    table_name = models.CharField(max_length=120, blank=True, default="")
    attribute_name = models.CharField(max_length=120, blank=True, default="")
    default_value = models.TextField(blank=True, default="")
    select_multiple = models.BooleanField(default=False)


class Form(BaseOpenmrsMetadata):
    """A versioned data-entry form."""

    version = models.CharField(max_length=50, default="1.0")
    build = models.IntegerField(null=True, blank=True)
    published = models.BooleanField(default=False)
    encounter_type = models.ForeignKey(
        "emr.EncounterType", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="forms",
    )

    class Meta:
        ordering = ["name", "version"]


class FormField(models.Model):
    """Places a field on a form, with ordering and optional nesting."""

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="form_fields")
    field = models.ForeignKey(Field, on_delete=models.PROTECT, related_name="form_fields")
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    field_number = models.IntegerField(null=True, blank=True)
    field_part = models.CharField(max_length=20, blank=True, default="")
    page_number = models.IntegerField(null=True, blank=True)
    sort_weight = models.FloatField(default=0)
    required = models.BooleanField(default=False)

    class Meta:
        ordering = ["page_number", "sort_weight"]

    def __str__(self):
        return f"{self.form_id}:{self.field_id}"


class FormResource(BaseOpenmrsData):
    """An arbitrary named resource attached to a form (e.g. an HFE schema)."""

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="resources")
    name = models.CharField(max_length=255)
    datatype = models.CharField(max_length=255, blank=True, default="")
    value_reference = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("form", "name")

    def __str__(self):
        return f"{self.form_id}:{self.name}"
