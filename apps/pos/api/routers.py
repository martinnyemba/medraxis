from apps.pos.api.views import (
    CustomerViewSet,
    PaymentViewSet,
    QuotationViewSet,
    SalesReturnViewSet,
    SaleViewSet,
)


def register_routes(router):
    router.register("pos/customers", CustomerViewSet, basename="customer")
    router.register("pos/sales", SaleViewSet, basename="sale")
    router.register("pos/payments", PaymentViewSet, basename="payment")
    router.register("pos/quotations", QuotationViewSet, basename="quotation")
    router.register("pos/sales-returns", SalesReturnViewSet, basename="sales-return")
