from apps.billing.api.views import (
    BillableServiceViewSet,
    InsuranceSchemeViewSet,
    PatientInsuranceViewSet,
)


def register_routes(router):
    router.register("billing/services", BillableServiceViewSet, basename="billable-service")
    router.register("billing/insurance-schemes", InsuranceSchemeViewSet, basename="insurance-scheme")
    router.register("billing/patient-insurance", PatientInsuranceViewSet, basename="patient-insurance")
