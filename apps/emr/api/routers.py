from apps.emr.api.views import (
    AllergyViewSet,
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
    PatientViewSet,
    RelationshipTypeViewSet,
    RelationshipViewSet,
    VisitTypeViewSet,
    VisitViewSet,
)


def register_routes(router):
    router.register("concepts", ConceptViewSet, basename="concept")
    router.register("patients", PatientViewSet, basename="patient")
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
    router.register("forms", FormViewSet, basename="form")
    router.register("allergies", AllergyViewSet, basename="allergy")
    router.register("conditions", ConditionViewSet, basename="condition")
    router.register("diagnoses", DiagnosisViewSet, basename="diagnosis")
