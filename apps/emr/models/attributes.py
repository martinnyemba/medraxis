"""Concrete attribute types/values for EMR owners.

Implements the OpenMRS customizable-attribute pattern (see
``apps.core.attributes``) for Visit, Location, Program enrolment and Concept --
the same mechanism ``PersonAttribute`` already provides for Person. Each owner
gets a ``*AttributeType`` (definition) and an ``*Attribute`` (value) so sites can
extend these entities without schema changes.
"""
from django.db import models

from apps.core.attributes import BaseAttribute, BaseAttributeType


class VisitAttributeType(BaseAttributeType):
    """Defines a custom attribute attachable to a Visit (e.g. 'Bed number')."""


class VisitAttribute(BaseAttribute):
    visit = models.ForeignKey(
        "emr.Visit", on_delete=models.CASCADE, related_name="attributes"
    )
    attribute_type = models.ForeignKey(
        VisitAttributeType, on_delete=models.PROTECT, related_name="values"
    )


class LocationAttributeType(BaseAttributeType):
    """Defines a custom attribute attachable to a Location (e.g. 'GPS', 'Phone')."""


class LocationAttribute(BaseAttribute):
    location = models.ForeignKey(
        "emr.Location", on_delete=models.CASCADE, related_name="attributes"
    )
    attribute_type = models.ForeignKey(
        LocationAttributeType, on_delete=models.PROTECT, related_name="values"
    )


class ConceptAttributeType(BaseAttributeType):
    """Defines a custom attribute attachable to a Concept."""


class ConceptAttribute(BaseAttribute):
    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.CASCADE, related_name="attributes"
    )
    attribute_type = models.ForeignKey(
        ConceptAttributeType, on_delete=models.PROTECT, related_name="values"
    )


class ProgramAttributeType(BaseAttributeType):
    """Defines a custom attribute attachable to a program enrolment."""


class PatientProgramAttribute(BaseAttribute):
    patient_program = models.ForeignKey(
        "emr.PatientProgram", on_delete=models.CASCADE, related_name="attributes"
    )
    attribute_type = models.ForeignKey(
        ProgramAttributeType, on_delete=models.PROTECT, related_name="values"
    )
