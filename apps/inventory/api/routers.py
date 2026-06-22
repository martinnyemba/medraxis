from apps.inventory.api.views import (
    ProductCategoryViewSet,
    ProductViewSet,
    PurchaseBillViewSet,
    PurchaseOrderViewSet,
    StockBatchViewSet,
    StockTransactionViewSet,
    SupplierViewSet,
    TaxRateViewSet,
    UnitOfMeasureViewSet,
)


def register_routes(router):
    router.register("inventory/categories", ProductCategoryViewSet, basename="product-category")
    router.register("inventory/units", UnitOfMeasureViewSet, basename="unit-of-measure")
    router.register("inventory/tax-rates", TaxRateViewSet, basename="tax-rate")
    router.register("inventory/suppliers", SupplierViewSet, basename="supplier")
    router.register("inventory/products", ProductViewSet, basename="product")
    router.register("inventory/batches", StockBatchViewSet, basename="stock-batch")
    router.register("inventory/transactions", StockTransactionViewSet, basename="stock-transaction")
    router.register("inventory/purchase-orders", PurchaseOrderViewSet, basename="purchase-order")
    router.register("inventory/purchase-bills", PurchaseBillViewSet, basename="purchase-bill")
