from apps.emr.api.views import (
    ConceptViewSet,
    EncounterViewSet,
    ObsViewSet,
    OrderViewSet,
    PatientViewSet,
    VisitViewSet,
)


def register_routes(router):
    router.register("concepts", ConceptViewSet, basename="concept")
    router.register("patients", PatientViewSet, basename="patient")
    router.register("visits", VisitViewSet, basename="visit")
    router.register("encounters", EncounterViewSet, basename="encounter")
    router.register("observations", ObsViewSet, basename="obs")
    router.register("orders", OrderViewSet, basename="order")
