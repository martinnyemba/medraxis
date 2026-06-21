"""EMR domain models (OpenMRS-inspired)."""
from apps.emr.models.clinical import Allergy, Condition, Diagnosis
from apps.emr.models.concept import (
    Concept,
    ConceptAnswer,
    ConceptClass,
    ConceptDatatype,
    ConceptMapping,
    ConceptName,
    ConceptReferenceTerm,
    ConceptSetMembership,
    ConceptSource,
)
from apps.emr.models.encounter import (
    Encounter,
    EncounterProvider,
    EncounterRole,
    EncounterType,
)
from apps.emr.models.location import Location, LocationTag
from apps.emr.models.obs import Obs
from apps.emr.models.order import CareSetting, Order, OrderType
from apps.emr.models.patient import Patient, PatientIdentifier, PatientIdentifierType
from apps.emr.models.person import (
    Person,
    PersonAddress,
    PersonAttribute,
    PersonAttributeType,
    PersonName,
)
from apps.emr.models.program import (
    PatientProgram,
    PatientState,
    Program,
    ProgramWorkflow,
    ProgramWorkflowState,
)
from apps.emr.models.visit import Visit, VisitType

__all__ = [
    "Allergy",
    "Condition",
    "Diagnosis",
    "Concept",
    "ConceptAnswer",
    "ConceptClass",
    "ConceptDatatype",
    "ConceptMapping",
    "ConceptName",
    "ConceptReferenceTerm",
    "ConceptSetMembership",
    "ConceptSource",
    "Encounter",
    "EncounterProvider",
    "EncounterRole",
    "EncounterType",
    "Location",
    "LocationTag",
    "Obs",
    "CareSetting",
    "Order",
    "OrderType",
    "Patient",
    "PatientIdentifier",
    "PatientIdentifierType",
    "Person",
    "PersonAddress",
    "PersonAttribute",
    "PersonAttributeType",
    "PersonName",
    "PatientProgram",
    "PatientState",
    "Program",
    "ProgramWorkflow",
    "ProgramWorkflowState",
    "Visit",
    "VisitType",
]
