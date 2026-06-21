"""POS services: invoice numbering, completion (stock issue) and payment."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.inventory import services as inventory_services
from apps.inventory.models import StockTransaction
from apps.pos.models import Payment, Sale, SaleLine


def next_invoice_number():
    today = timezone.now().strftime("%Y%m%d")
    count = Sale.objects.filter(invoice_number__startswith=f"INV-{today}").count()
    return f"INV-{today}-{count + 1:05d}"


@transaction.atomic
def complete_sale(sale: Sale):
    """Finalise a sale: issue stock for product lines, recompute totals.

    Idempotent per line via the ``issued_stock`` flag, so re-completing a sale
    will not double-deduct inventory.
    """
    for line in sale.lines.select_for_update():
        if line.line_type == SaleLine.LineType.PRODUCT and line.product_id and not line.issued_stock:
            inventory_services.issue_stock(
                product=line.product, location=sale.location, quantity=line.quantity,
                transaction_type=StockTransaction.TxnType.SALE,
                reference_type="SALE", reference_id=sale.invoice_number,
            )
            line.issued_stock = True
            line.save(update_fields=["issued_stock"])

    sale.recalculate()
    sale.status = Sale.Status.COMPLETED
    _sync_payment_status(sale)
    sale.save()
    return sale


@transaction.atomic
def add_payment(sale: Sale, *, method, amount, reference="", received_by=None):
    """Record a payment and update the sale's paid amount and status."""
    amount = Decimal(str(amount))
    payment = Payment.objects.create(
        sale=sale, method=method, amount=amount, reference=reference,
        received_by=received_by, status=Payment.Status.PAID,
    )
    sale.amount_paid = sum((p.amount for p in sale.payments.filter(status=Payment.Status.PAID)), Decimal("0"))
    _sync_payment_status(sale)
    sale.save(update_fields=["amount_paid", "status", "updated_at"])
    return payment


def _sync_payment_status(sale: Sale):
    """Derive PAID / PARTIALLY_PAID from totals (leaves VOID/DRAFT untouched)."""
    if sale.status in (Sale.Status.VOID, Sale.Status.REFUNDED, Sale.Status.DRAFT):
        return
    if sale.amount_paid <= 0:
        sale.status = Sale.Status.COMPLETED
    elif sale.amount_paid < sale.grand_total:
        sale.status = Sale.Status.PARTIALLY_PAID
    else:
        sale.status = Sale.Status.PAID
