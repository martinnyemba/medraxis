from apps.finance.api.views import (
    AccountTransactionViewSet,
    BusinessReportsViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    FinancialAccountViewSet,
    PartyLedgerViewSet,
    SupplierPaymentViewSet,
    TaxComponentViewSet,
)


def register_routes(router):
    router.register("finance/accounts", FinancialAccountViewSet, basename="financial-account")
    router.register("finance/account-transactions", AccountTransactionViewSet,
                    basename="account-transaction")
    router.register("finance/expense-categories", ExpenseCategoryViewSet,
                    basename="expense-category")
    router.register("finance/expenses", ExpenseViewSet, basename="expense")
    router.register("finance/supplier-payments", SupplierPaymentViewSet,
                    basename="supplier-payment")
    router.register("finance/tax-components", TaxComponentViewSet, basename="tax-component")
    router.register("finance/party-ledger", PartyLedgerViewSet, basename="party-ledger")
    router.register("finance/reports", BusinessReportsViewSet, basename="business-report")
