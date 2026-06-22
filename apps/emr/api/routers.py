from apps.emr.api.views import (
    AllergyViewSet,
    CohortMembershipViewSet,
    CohortViewSet,
    ConceptViewSet,
    ConditionViewSet,
    DiagnosisViewSet,
    DrugViewSet,
    EncounterTypeViewSet,
    EncounterViewSet,
    FormViewSet,
    LocationViewSet,
    ObsViewSet,
    OrderFrequencyViewSet,
    OrderViewSet,
    PatientIdentifierTypeViewSet,
    PatientIdentifierViewSet,
    PatientProgramViewSet,
    PatientStateViewSet,
    PatientViewSet,
    PersonAddressViewSet,
    PersonAttributeTypeViewSet,
    PersonAttributeViewSet,
    PersonNameViewSet,
    ProgramViewSet,
    ProgramWorkflowStateViewSet,
    ProgramWorkflowViewSet,
    RelationshipTypeViewSet,
    RelationshipViewSet,
    VisitTypeViewSet,
    VisitViewSet,
)


def register_routes(router):
    router.register("concepts", ConceptViewSet, basename="concept")
    router.register("patients", PatientViewSet, basename="patient")
    router.register("person-names", PersonNameViewSet, basename="person-name")
    router.register("patient-identifiers", PatientIdentifierViewSet, basename="patient-identifier")
    router.register(
        "patient-identifier-types", PatientIdentifierTypeViewSet, basename="patient-identifier-type"
    )
    router.register("person-addresses", PersonAddressViewSet, basename="person-address")
    router.register("person-attribute-types", PersonAttributeTypeViewSet, basename="person-attribute-type")
    router.register("person-attributes", PersonAttributeViewSet, basename="person-attribute")
    router.register("visit-types", VisitTypeViewSet, basename="visit-type")
    router.register("encounter-types", EncounterTypeViewSet, basename="encounter-type")
    router.register("locations", LocationViewSet, basename="location")
    router.register("visits", VisitViewSet, basename="visit")
    router.register("encounters", EncounterViewSet, basename="encounter")
    router.register("observations", ObsViewSet, basename="obs")
    router.register("orders", OrderViewSet, basename="order")
    router.register("drugs", DrugViewSet, basename="drug")
    router.register("order-frequencies", OrderFrequencyViewSet, basename="order-frequency")
    router.register("relationship-types", RelationshipTypeViewSet, basename="relationship-type")
    router.register("relationships", RelationshipViewSet, basename="relationship")
    router.register("cohorts", CohortViewSet, basename="cohort")
    router.register("cohort-memberships", CohortMembershipViewSet, basename="cohort-membership")
    router.register("forms", FormViewSet, basename="form")
    router.register("allergies", AllergyViewSet, basename="allergy")
    router.register("conditions", ConditionViewSet, basename="condition")
    router.register("diagnoses", DiagnosisViewSet, basename="diagnosis")
    router.register("programs", ProgramViewSet, basename="program")
    router.register("program-workflows", ProgramWorkflowViewSet, basename="program-workflow")
    router.register(
        "program-workflow-states", ProgramWorkflowStateViewSet, basename="program-workflow-state"
    )
    router.register("patient-programs", PatientProgramViewSet, basename="patient-program")
    router.register("patient-states", PatientStateViewSet, basename="patient-state")
