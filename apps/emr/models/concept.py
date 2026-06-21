"""The Concept dictionary -- the semantic backbone of OpenMRS.

Almost everything observable or orderable in the system (a diagnosis, a lab
analyte, a vital sign, a drug, a question and its coded answers) is defined
once as a ``Concept``. Observations, orders and lab results then *reference*
concepts rather than storing free text, which is what makes the data
analysable, interoperable and FHIR/LOINC-mappable.
"""
from django.db import models

from apps.core.models import BaseOpenmrsMetadata


class ConceptClass(BaseOpenmrsMetadata):
    """Classifies a concept: Diagnosis, Test, Drug, Finding, Question, ..."""

    class Meta:
        verbose_name_plural = "concept classes"


class ConceptDatatype(BaseOpenmrsMetadata):
    """The value type a concept's observations carry.

    e.g. Numeric, Coded, Text, Date, Datetime, Boolean, Complex.
    """

    hl7_abbreviation = models.CharField(max_length=10, blank=True, default="")


class Concept(BaseOpenmrsMetadata):
    """A single reusable clinical/laboratory/business idea.

    The ``name`` field (from ``BaseOpenmrsMetadata``) holds the fully-specified
    preferred name; locale-specific synonyms live in :class:`ConceptName`.
    """

    short_name = models.CharField(max_length=255, blank=True, default="")
    concept_class = models.ForeignKey(
        ConceptClass, on_delete=models.PROTECT, related_name="concepts"
    )
    datatype = models.ForeignKey(
        ConceptDatatype, on_delete=models.PROTECT, related_name="concepts"
    )
    is_set = models.BooleanField(
        default=False, help_text="True if this concept groups other concepts (a panel/set)."
    )
    version = models.CharField(max_length=50, blank=True, default="")

    # Numeric metadata (OpenMRS ConceptNumeric). Null for non-numeric concepts.
    units = models.CharField(max_length=50, blank=True, default="")
    hi_normal = models.FloatField(null=True, blank=True)
    low_normal = models.FloatField(null=True, blank=True)
    hi_critical = models.FloatField(null=True, blank=True)
    low_critical = models.FloatField(null=True, blank=True)
    hi_absolute = models.FloatField(null=True, blank=True)
    low_absolute = models.FloatField(null=True, blank=True)
    allow_decimal = models.BooleanField(default=True)

    set_members = models.ManyToManyField(
        "self",
        through="ConceptSetMembership",
        symmetrical=False,
        related_name="member_of_sets",
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["concept_class", "datatype"])]

    def __str__(self):
        return self.name


class ConceptName(BaseOpenmrsMetadata):
    """A localized name/synonym for a concept."""

    class NameType(models.TextChoices):
        FULLY_SPECIFIED = "FULLY_SPECIFIED", "Fully specified"
        SHORT = "SHORT", "Short"
        SYNONYM = "SYNONYM", "Synonym"

    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="names")
    locale = models.CharField(max_length=20, default="en", db_index=True)
    name_type = models.CharField(
        max_length=20, choices=NameType.choices, default=NameType.SYNONYM
    )
    locale_preferred = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["concept", "locale"])]


class ConceptAnswer(BaseOpenmrsMetadata):
    """A valid coded answer for a question-type concept."""

    question = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="answers"
    )
    answer_concept = models.ForeignKey(
        Concept, on_delete=models.PROTECT, related_name="answer_to", null=True, blank=True
    )
    sort_weight = models.FloatField(default=0)

    class Meta:
        ordering = ["sort_weight"]


class ConceptSetMembership(models.Model):
    """Ordered membership of a concept within a concept set/panel."""

    concept_set = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="set_memberships"
    )
    member = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="membership_in_sets"
    )
    sort_weight = models.FloatField(default=0)

    class Meta:
        ordering = ["sort_weight"]
        unique_together = ("concept_set", "member")


class ConceptSource(BaseOpenmrsMetadata):
    """An external terminology (LOINC, SNOMED CT, ICD-10, CIEL, RxNorm)."""

    hl7_code = models.CharField(max_length=50, blank=True, default="")


class ConceptReferenceTerm(BaseOpenmrsMetadata):
    """A code within an external source, used for FHIR/HL7 interoperability."""

    source = models.ForeignKey(
        ConceptSource, on_delete=models.PROTECT, related_name="reference_terms"
    )
    code = models.CharField(max_length=255, db_index=True)

    class Meta:
        unique_together = ("source", "code")


class ConceptMapping(models.Model):
    """Maps a local concept to an external reference term."""

    class MapType(models.TextChoices):
        SAME_AS = "SAME-AS", "Same as"
        NARROWER_THAN = "NARROWER-THAN", "Narrower than"
        BROADER_THAN = "BROADER-THAN", "Broader than"
        RELATED_TO = "RELATED-TO", "Related to"

    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="mappings")
    reference_term = models.ForeignKey(
        ConceptReferenceTerm, on_delete=models.PROTECT, related_name="concept_mappings"
    )
    map_type = models.CharField(
        max_length=20, choices=MapType.choices, default=MapType.SAME_AS
    )

    class Meta:
        unique_together = ("concept", "reference_term", "map_type")
