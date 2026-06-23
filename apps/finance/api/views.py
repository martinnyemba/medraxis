from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.finance import models as m
from apps.finance import services
from apps.finance.api.serializers import (
    AccountTransactionSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    FinancialAccountSerializer,
    PartyLedgerEntrySerializer,
    SupplierPaymentSerializer,
    TaxComponentSerializer,
)
from apps.finance.ledger import party_balance
from apps.finance import reports
from apps.tenancy.mixins import TenantResolverMixin, TenantScopedQuerySetMixin


class FinancialAccountViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.FinancialAccount.objects.all()
    serializer_class = FinancialAccountSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "account_number", "bank_name"]
    filterset_fields = ["account_type", "is_default"]

    def perform_create(self, serializer):
        account = serializer.save()
        # Seed the running balance from the opening balance.
        if account.opening_balance and not account.current_balance:
            account.current_balance = account.opening_balance
            account.save(update_fields=["current_balance"])

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        account = self.get_object()
        page = self.paginate_queryset(account.transactions.all())
        return self.get_paginated_response(
            AccountTransactionSerializer(page, many=True).data)


class AccountTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = m.AccountTransaction.objects.select_related("account")
    serializer_class = AccountTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["account", "direction"]


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = m.ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]


class ExpenseViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.Expense.objects.select_related("category", "account", "supplier")
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "account", "supplier"]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        expense = services.record_expense(
            category=d["category"], amount=d["amount"], expense_date=d.get("expense_date"),
            account=d.get("account"), supplier=d.get("supplier"),
            tax_amount=d.get("tax_amount", 0), payment_method=d.get("payment_method", ""),
            note=d.get("note", ""),
            organization=getattr(request, "organization", None),
        )
        return Response(self.get_serializer(expense).data, status=status.HTTP_201_CREATED)


class SupplierPaymentViewSet(TenantScopedQuerySetMixin, viewsets.ModelViewSet):
    queryset = m.SupplierPayment.objects.select_related("supplier", "account")
    serializer_class = SupplierPaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["supplier", "account"]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        allocations = [
            (a["purchase_bill"], a["amount"]) for a in d.get("allocations", [])
        ]
        payment = services.pay_supplier(
            supplier=d["supplier"], amount=d["amount"], account=d.get("account"),
            paid_on=d.get("paid_on"), method=d.get("method", "CASH"),
            reference=d.get("reference", ""), allocations=allocations,
            note=d.get("note", ""), organization=getattr(request, "organization", None),
        )
        return Response(self.get_serializer(payment).data, status=status.HTTP_201_CREATED)


class TaxComponentViewSet(viewsets.ModelViewSet):
    queryset = m.TaxComponent.objects.select_related("tax_rate")
    serializer_class = TaxComponentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["tax_rate", "component_type"]


class PartyLedgerViewSet(viewsets.ViewSet):
    """Party statements & outstanding balances (customers/suppliers/clients)."""

    permission_classes = [IsAuthenticated]

    _PARTY_MODELS = {
        "customer": ("pos", "customer"),
        "supplier": ("inventory", "supplier"),
    }

    def _resolve_party(self, party_type, party_id):
        mapping = self._PARTY_MODELS.get(party_type)
        if mapping is None:
            raise ValidationError(
                f"party_type must be one of: {', '.join(self._PARTY_MODELS)}")
        ct = ContentType.objects.get(app_label=mapping[0], model=mapping[1])
        model = ct.model_class()
        party = model.objects.filter(pk=party_id).first()
        if party is None:
            raise ValidationError(f"{party_type} {party_id} not found.")
        return party

    @action(detail=False, methods=["get"])
    def statement(self, request):
        """GET ?party_type=customer&party_id=1 -> ledger entries + balance."""
        party = self._resolve_party(
            request.query_params.get("party_type"),
            request.query_params.get("party_id"))
        from apps.finance.ledger import statement
        entries = statement(party)
        return Response({
            "party_type": request.query_params.get("party_type"),
            "party_id": party.pk,
            "balance": party_balance(party),
            "entries": PartyLedgerEntrySerializer(entries, many=True).data,
        })

    @action(detail=False, methods=["get"])
    def balance(self, request):
        party = self._resolve_party(
            request.query_params.get("party_type"),
            request.query_params.get("party_id"))
        return Response({"balance": party_balance(party)})


class BusinessReportsViewSet(TenantResolverMixin, viewsets.ViewSet):
    """Owner-facing business reports: summary, day book and outstanding.

    Read-only aggregations scoped to the active tenant; see
    :mod:`apps.finance.reports`.
    """

    permission_classes = [IsAuthenticated]

    def _org(self, request):
        return getattr(request, "organization", None)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """GET ?from=YYYY-MM-DD&to=YYYY-MM-DD -> period revenue/expenses/net."""
        today = timezone.now().date()
        date_to = reports.parse_date(request.query_params.get("to"), today)
        date_from = reports.parse_date(
            request.query_params.get("from"), date_to.replace(day=1))
        return Response(reports.business_summary(self._org(request), date_from, date_to))

    @action(detail=False, methods=["get"])
    def day_book(self, request):
        """GET ?date=YYYY-MM-DD -> money in/out for the day."""
        date = reports.parse_date(request.query_params.get("date"))
        return Response(reports.day_book(self._org(request), date))

    @action(detail=False, methods=["get"])
    def outstanding(self, request):
        """Receivables and payables across all parties."""
        return Response(reports.outstanding(self._org(request)))
