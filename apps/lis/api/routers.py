from apps.lis.api.views import (
    AnalyzerViewSet,
    LabResultViewSet,
    LabSectionViewSet,
    LabTestViewSet,
    SpecimenViewSet,
    TestOrderViewSet,
)


def register_routes(router):
    router.register("lab/sections", LabSectionViewSet, basename="lab-section")
    router.register("lab/tests", LabTestViewSet, basename="lab-test")
    router.register("lab/test-orders", TestOrderViewSet, basename="test-order")
    router.register("lab/specimens", SpecimenViewSet, basename="specimen")
    router.register("lab/results", LabResultViewSet, basename="lab-result")
    router.register("lab/analyzers", AnalyzerViewSet, basename="analyzer")
