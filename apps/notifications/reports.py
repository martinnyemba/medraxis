"""Report generators run by :func:`apps.notifications.tasks.generate_report_task`.

Each generator returns ``(filename, content_bytes, row_count)``. Reports are
CSV for portability; they honour the requesting organization for tenant
isolation. Register new reports in ``REPORT_REGISTRY``.
"""
import csv
import io
from datetime import datetime

from django.utils import timezone


def _csv(header, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    count = 0
    for row in rows:
        writer.writerow(row)
        count += 1
    return buffer.getvalue().encode("utf-8"), count


def _parse_date(value):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def daily_sales(parameters, organization):
    """Invoice-level sales summary, optionally filtered by date range."""
    from apps.pos.models import Sale

    qs = Sale.objects.all()
    if organization is not None:
        qs = qs.filter(organization=organization)
    start = _parse_date(parameters.get("start"))
    end = _parse_date(parameters.get("end"))
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    header = ["invoice_number", "date", "status", "subtotal", "tax_total",
              "grand_total", "amount_paid"]
    rows = (
        [s.invoice_number, s.created_at.date().isoformat(), s.status,
         s.subtotal, s.tax_total, s.grand_total, s.amount_paid]
        for s in qs.order_by("created_at")
    )
    content, count = _csv(header, rows)
    return f"daily_sales_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


def stock_valuation(parameters, organization):
    """Current on-hand quantity and cost valuation per product batch."""
    from apps.inventory.models import StockBatch

    qs = StockBatch.objects.select_related("product", "location").filter(quantity_on_hand__gt=0)
    if organization is not None:
        qs = qs.filter(product__organization=organization)

    header = ["sku", "product", "location", "batch", "expiry", "qty", "cost_price", "value"]
    rows = (
        [b.product.sku, b.product.name, str(b.location_id), b.batch_number,
         b.expiry_date.isoformat() if b.expiry_date else "",
         b.quantity_on_hand, b.cost_price, b.quantity_on_hand * b.cost_price]
        for b in qs
    )
    content, count = _csv(header, rows)
    return f"stock_valuation_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


def expiring_stock(parameters, organization):
    """Batches expiring within ``days`` (default 90)."""
    from apps.inventory.services import expiring_soon

    days = int(parameters.get("days", 90))
    qs = expiring_soon(days=days)
    if organization is not None:
        qs = qs.filter(product__organization=organization)

    header = ["sku", "product", "batch", "expiry", "qty", "location"]
    rows = (
        [b.product.sku, b.product.name, b.batch_number,
         b.expiry_date.isoformat() if b.expiry_date else "",
         b.quantity_on_hand, str(b.location_id)]
        for b in qs
    )
    content, count = _csv(header, rows)
    return f"expiring_stock_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


def lab_turnaround(parameters, organization):
    """Released lab results with order-to-release turnaround in hours."""
    from apps.lis.models import LabResult

    qs = LabResult.objects.select_related("test_order", "analyte").filter(
        status=LabResult.Status.RELEASED
    )
    if organization is not None:
        qs = qs.filter(test_order__organization=organization)

    header = ["accession_order", "analyte", "verified_at", "released_value", "flag"]
    rows = (
        [r.test_order.order_number, r.analyte.name,
         r.verified_at.isoformat() if r.verified_at else "",
         r.value_numeric if r.value_numeric is not None else r.value_text, r.flag]
        for r in qs
    )
    content, count = _csv(header, rows)
    return f"lab_turnaround_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


REPORT_REGISTRY = {
    "daily_sales": daily_sales,
    "stock_valuation": stock_valuation,
    "expiring_stock": expiring_stock,
    "lab_turnaround": lab_turnaround,
    "expense_summary": lambda p, o: _expense_summary(p, o),
    "outstanding_balances": lambda p, o: _outstanding_balances(p, o),
    "day_book": lambda p, o: _day_book(p, o),
}


def _expense_summary(parameters, organization):
    """Total expenses per category over an optional date range."""
    from django.db.models import Sum
    from apps.finance.models import Expense

    qs = Expense.objects.all()
    if organization is not None:
        qs = qs.filter(organization=organization)
    start = _parse_date(parameters.get("start"))
    end = _parse_date(parameters.get("end"))
    if start:
        qs = qs.filter(expense_date__gte=start)
    if end:
        qs = qs.filter(expense_date__lte=end)
    rows = (
        [r["category__name"], r["total"]]
        for r in qs.values("category__name").annotate(total=Sum("amount")).order_by("-total")
    )
    content, count = _csv(["category", "total"], rows)
    return f"expense_summary_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


def _outstanding_balances(parameters, organization):
    """Current receivable/payable balance per party (from the party ledger)."""
    from apps.finance.models import PartyLedgerEntry

    qs = PartyLedgerEntry.objects.all()
    if organization is not None:
        qs = qs.filter(organization=organization)

    # Latest balance per party is the most recent entry's running balance.
    latest = {}
    for e in qs.order_by("party_content_type", "party_object_id", "entry_date", "id"):
        latest[(e.party_content_type_id, e.party_object_id)] = (e.party, e.balance)
    rows = []
    for (_, _), (party, balance) in latest.items():
        if balance == 0:
            continue
        kind = "receivable" if balance > 0 else "payable"
        rows.append([str(party), kind, abs(balance)])
    content, count = _csv(["party", "type", "amount"], rows)
    return f"outstanding_{timezone.now():%Y%m%d_%H%M%S}.csv", content, count


def _day_book(parameters, organization):
    """All money movements (in/out) on a given date (default today)."""
    from apps.finance.models import AccountTransaction

    day = _parse_date(parameters.get("date")) or timezone.now().date()
    qs = AccountTransaction.objects.filter(occurred_at__date=day).select_related("account")
    if organization is not None:
        qs = qs.filter(account__organization=organization)
    rows = (
        [t.occurred_at.isoformat(), t.account.name, t.direction, t.amount,
         t.balance_after, t.reference_type, t.reference_id]
        for t in qs.order_by("occurred_at")
    )
    header = ["time", "account", "direction", "amount", "balance_after", "ref_type", "ref_id"]
    content, count = _csv(header, rows)
    return f"day_book_{day:%Y%m%d}.csv", content, count


def run_report(report_type, parameters, organization):
    generator = REPORT_REGISTRY.get(report_type)
    if generator is None:
        raise ValueError(f"Unknown report type: {report_type}")
    return generator(parameters or {}, organization)
