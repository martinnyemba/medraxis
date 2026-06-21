"""EMR domain models (OpenMRS-inspired)."""
from apps.emr.models.attributes import (
    ConceptAttribute,
    ConceptAttributeType,
    LocationAttribute,
    LocationAttributeType,
    PatientProgramAttribute,
    ProgramAttributeType,
    VisitAttribute,
    VisitAttributeType,
)
from apps.emr.models.clinical import Allergy, AllergyReaction, Condition, Diagnosis
from apps.emr.models.cohort import Cohort, CohortMembership
from apps.emr.models.concept import (
    Concept,
    ConceptAnswer,
    ConceptClass,
    ConceptDatatype,
    ConceptDescription,
    ConceptMapping,
    ConceptMapType,
    ConceptName,
    ConceptProposal,
    ConceptReferenceTerm,
    ConceptReferenceTermMap,
    ConceptSetMembership,
    ConceptSource,
)
from apps.emr.models.drug import Drug, DrugIngredient
from apps.emr.models.encounter import (
    Encounter,
    EncounterProvider,
    EncounterRole,
    EncounterType,
)
from apps.emr.models.forms import Field, FieldType, Form, FormField, FormResource
from apps.emr.models.location import Location, LocationTag
from apps.emr.models.obs import Obs
from apps.emr.models.order import (
    CareSetting,
    Order,
    OrderFrequency,
    OrderGroup,
    OrderSet,
    OrderSetMember,
    OrderType,
)
from apps.emr.models.patient import Patient, PatientIdentifier, PatientIdentifierType
from apps.emr.models.person import (
    Person,
    PersonAddress,
    PersonAttribute,
    PersonAttributeType,
    PersonName,
)
from apps.emr.models.program import (
    ConceptStateConversion,
    PatientProgram,
    PatientState,
    Program,
    ProgramWorkflow,
    ProgramWorkflowState,
)
from apps.emr.models.relationship import Relationship, RelationshipType
from apps.emr.models.visit import Visit, VisitType

__all__ = [
    # attributes
    "ConceptAttribute", "ConceptAttributeType", "LocationAttribute",
    "LocationAttributeType", "PatientProgramAttribute", "ProgramAttributeType",
    "VisitAttribute", "VisitAttributeType",
    # clinical
    "Allergy", "AllergyReaction", "Condition", "Diagnosis",
    # cohort
    "Cohort", "CohortMembership",
    # concept
    "Concept", "ConceptAnswer", "ConceptClass", "ConceptDatatype",
    "ConceptDescription", "ConceptMapping", "ConceptMapType", "ConceptName",
    "ConceptProposal", "ConceptReferenceTerm", "ConceptReferenceTermMap",
    "ConceptSetMembership", "ConceptSource",
    # drug
    "Drug", "DrugIngredient",
    # encounter
    "Encounter", "EncounterProvider", "EncounterRole", "EncounterType",
    # forms
    "Field", "FieldType", "Form", "FormField", "FormResource",
    # location
    "Location", "LocationTag",
    # obs
    "Obs",
    # order
    "CareSetting", "Order", "OrderFrequency", "OrderGroup", "OrderSet",
    "OrderSetMember", "OrderType",
    # patient
    "Patient", "PatientIdentifier", "PatientIdentifierType",
    # person
    "Person", "PersonAddress", "PersonAttribute", "PersonAttributeType", "PersonName",
    # program
    "ConceptStateConversion", "PatientProgram", "PatientState", "Program",
    "ProgramWorkflow", "ProgramWorkflowState",
    # relationship
    "Relationship", "RelationshipType",
    # visit
    "Visit", "VisitType",
]
