"""Business reports (Valeron/Vyapar-inspired): summary, day book, outstanding.

Read-only aggregations over the sales, expense, money-account and party ledgers
that already exist, turning recorded transactions into the running-business views
an owner needs: a period **summary** (revenue/collections/expenses/net),
a **day book** (cash & bank movements for a date), and **outstanding**
receivables/payables across parties. All figures are scoped to the active tenant.
"""
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import (
    AccountTransaction,
    Expense,
    PartyLedgerEntry,
    SupplierPayment,
)
from apps.pos.models import Payment, Sale

ZERO = Decimal("0")


def _d(value):
    """Normalise an aggregate (which may be ``None``) to a Decimal."""
    return value if value is not None else ZERO


def _scope(qs, organization, field="organization"):
    return qs.filter(**{field: organization}) if organization is not None else qs


def business_summary(organization, date_from, date_to):
    """Revenue, collections, expenses and net cash for a date range.

    * **revenue** -- billed value of non-draft, non-void sales created in range.
    * **collected** -- payments received (money in) in range.
    * **expenses** / **supplier_payments** -- money out in range.
    * **net_cash** -- collected minus money out.
    """
    sales = _scope(
        Sale.objects.exclude(status__in=[Sale.Status.DRAFT, Sale.Status.VOID]),
        organization,
    ).filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
    revenue = _d(sales.aggregate(revenue=Sum("grand_total"))["revenue"])
    sales_count = sales.count()

    collected = _d(
        _scope(
            Payment.objects.filter(status=Payment.Status.PAID),
            organization,
            field="sale__organization",
        )
        .filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
        .aggregate(total=Sum("amount"))["total"]
    )

    expense_qs = _scope(Expense.objects.all(), organization).filter(
        expense_date__gte=date_from, expense_date__lte=date_to
    )
    expenses_total = _d(expense_qs.aggregate(total=Sum("amount"))["total"]) + _d(
        expense_qs.aggregate(total=Sum("tax_amount"))["total"]
    )

    supplier_payments = _d(
        _scope(SupplierPayment.objects.all(), organization)
        .filter(paid_on__gte=date_from, paid_on__lte=date_to)
        .aggregate(total=Sum("amount"))["total"]
    )

    # Expense breakdown by category (largest first).
    by_category = [
        {"category": row["category__name"], "amount": str(_d(row["total"]))}
        for row in expense_qs.values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    ]

    return {
        "date_from": str(date_from),
        "date_to": str(date_to),
        "sales_count": sales_count,
        "revenue": str(revenue),
        "collected": str(collected),
        "expenses": str(expenses_total),
        "supplier_payments": str(supplier_payments),
        "net_cash": str(collected - expenses_total - supplier_payments),
        "expenses_by_category": by_category,
    }


def day_book(organization, date):
    """All money-account movements on a date, split into money in / money out."""
    txns = _scope(
        AccountTransaction.objects.select_related("account"),
        organization,
        field="account__organization",
    ).filter(occurred_at__date=date).order_by("occurred_at", "id")

    money_in = ZERO
    money_out = ZERO
    rows = []
    for t in txns:
        if t.direction == AccountTransaction.Direction.IN:
            money_in += t.amount
        else:
            money_out += t.amount
        rows.append({
            "id": t.id,
            "account": t.account.name,
            "direction": t.direction,
            "amount": str(t.amount),
            "balance_after": str(t.balance_after),
            "reference_type": t.reference_type,
            "reference_id": t.reference_id,
            "note": t.note,
            "occurred_at": t.occurred_at.isoformat(),
        })

    return {
        "date": str(date),
        "money_in": str(money_in),
        "money_out": str(money_out),
        "net": str(money_in - money_out),
        "entries": rows,
    }


def outstanding(organization):
    """Receivables and payables from the latest balance carried per party.

    A positive party balance is a receivable (they owe us); a negative balance
    is a payable (we owe them). Returns per-party rows and totals.
    """
    entries = _scope(PartyLedgerEntry.objects.all(), organization)
    party_keys = entries.values_list(
        "party_content_type", "party_object_id"
    ).distinct()

    receivables = []
    payables = []
    receivable_total = ZERO
    payable_total = ZERO
    ct_cache = {}

    for ct_id, obj_id in party_keys:
        last = (
            entries.filter(party_content_type=ct_id, party_object_id=obj_id)
            .order_by("-entry_date", "-id")
            .first()
        )
        if last is None or last.balance == ZERO:
            continue
        ct = ct_cache.get(ct_id)
        if ct is None:
            ct = ContentType.objects.get_for_id(ct_id)
            ct_cache[ct_id] = ct
        party = ct.model_class().objects.filter(pk=obj_id).first()
        row = {
            "party_type": ct.model,
            "party_id": obj_id,
            "party_name": str(party) if party is not None else f"{ct.model} {obj_id}",
            "balance": str(abs(last.balance)),
        }
        if last.balance > ZERO:
            receivable_total += last.balance
            receivables.append(row)
        else:
            payable_total += -last.balance
            payables.append(row)

    receivables.sort(key=lambda r: Decimal(r["balance"]), reverse=True)
    payables.sort(key=lambda r: Decimal(r["balance"]), reverse=True)

    return {
        "receivable_total": str(receivable_total),
        "payable_total": str(payable_total),
        "receivables": receivables,
        "payables": payables,
    }


def parse_date(value, default=None):
    """Parse an ISO date string, falling back to ``default`` or today."""
    if not value:
        return default or timezone.now().date()
    from datetime import date

    return date.fromisoformat(value)
