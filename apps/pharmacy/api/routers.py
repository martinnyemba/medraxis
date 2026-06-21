from apps.pharmacy.api.views import DispenseViewSet, DrugOrderViewSet


def register_routes(router):
    router.register("pharmacy/drug-orders", DrugOrderViewSet, basename="drug-order")
    router.register("pharmacy/dispenses", DispenseViewSet, basename="dispense")
