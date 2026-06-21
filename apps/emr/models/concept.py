"""The Concept dictionary -- the semantic backbone of OpenMRS.

Almost everything observable or orderable in the system (a diagnosis, a lab
analyte, a vital sign, a drug, a question and its coded answers) is defined
once as a ``Concept``. Observations, orders and lab results then *reference*
concepts rather than storing free text, which is what makes the data
analysable, interoperable and FHIR/LOINC-mappable.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


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


class ConceptDescription(BaseOpenmrsMetadata):
    """A locale-specific free-text description of a concept.

    OpenMRS separates short synonyms (``ConceptName``) from longer prose
    descriptions; this is the latter, one per locale.
    """

    concept = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="descriptions"
    )
    locale = models.CharField(max_length=20, default="en", db_index=True)
    description_text = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["concept", "locale"])]


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

    def __str__(self):
        return f"{self.member_id} in set {self.concept_set_id}"


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
    map_type_ref = models.ForeignKey(
        "emr.ConceptMapType", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="concept_mappings",
        help_text="Optional rich map type (extends the simple map_type choices).",
    )

    class Meta:
        unique_together = ("concept", "reference_term", "map_type")

    def __str__(self):
        return f"{self.concept_id} {self.map_type} {self.reference_term_id}"


class ConceptMapType(BaseOpenmrsMetadata):
    """A configurable mapping relationship (OpenMRS ``ConceptMapType``).

    e.g. SAME-AS, NARROWER-THAN, BROADER-THAN, ASSOCIATED-WITH. Lets sites add
    mapping semantics beyond the built-in choices.
    """

    is_hidden = models.BooleanField(default=False)
    weight = models.IntegerField(default=0)

    class Meta:
        ordering = ["weight", "name"]


class ConceptReferenceTermMap(models.Model):
    """A typed mapping between two reference terms (term-to-term).

    Mirrors OpenMRS ``ConceptReferenceTermMap`` -- e.g. a LOINC term mapped
    SAME-AS a CIEL term -- enabling terminology crosswalks.
    """

    term_a = models.ForeignKey(
        ConceptReferenceTerm, on_delete=models.CASCADE, related_name="maps_from"
    )
    term_b = models.ForeignKey(
        ConceptReferenceTerm, on_delete=models.CASCADE, related_name="maps_to"
    )
    map_type = models.ForeignKey(
        ConceptMapType, on_delete=models.PROTECT, related_name="term_maps"
    )

    class Meta:
        unique_together = ("term_a", "term_b", "map_type")

    def __str__(self):
        return f"{self.term_a_id} {self.map_type_id} {self.term_b_id}"


class ConceptProposal(BaseOpenmrsData):
    """A proposed new concept/answer captured during data entry.

    Mirrors OpenMRS ``ConceptProposal``: when a clinician enters a value that is
    not yet in the dictionary, it is recorded for a dictionary manager to review
    and either map to an existing concept or promote to a new one.
    """

    class State(models.TextChoices):
        UNMAPPED = "UNMAPPED", "Unmapped"
        CONCEPT = "CONCEPT", "Mapped to concept"
        SYNONYM = "SYNONYM", "Mapped as synonym"
        REJECTED = "REJECTED", "Rejected"

    original_text = models.CharField(max_length=255)
    encounter = models.ForeignKey(
        "emr.Encounter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="concept_proposals",
    )
    obs_concept = models.ForeignKey(
        Concept, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="proposals_as_question",
    )
    mapped_concept = models.ForeignKey(
        Concept, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="proposals_mapped",
    )
    state = models.CharField(max_length=20, choices=State.choices, default=State.UNMAPPED)
    comments = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Proposal: {self.original_text} [{self.state}]"
