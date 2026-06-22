"""POS services: invoice numbering, completion (stock issue) and payment."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.services import audit as audit_services
from apps.inventory import services as inventory_services
from apps.inventory.models import StockTransaction
from apps.pos.models import Payment, Sale, SaleLine


def next_invoice_number():
    today = timezone.now().strftime("%Y%m%d")
    count = Sale.objects.filter(invoice_number__startswith=f"INV-{today}").count()
    return f"INV-{today}-{count + 1:05d}"


def _billing_party(sale: Sale):
    """The party whose ledger a sale affects: the B2B client or retail customer.

    A bare patient/walk-in cash sale has no party account, so no receivable is
    tracked -- the money simply lands in a financial account.
    """
    return sale.client or sale.customer


@transaction.atomic
def reprice_sale(sale: Sale):
    """Re-resolve catalogue prices for every line and recompute totals.

    Forces resolution (clears existing price/tax first) so a newly-set client
    rate card is applied. Only meaningful before completion/payment.
    """
    from apps.pos.pricing import price_line

    for line in sale.lines.all():
        line.unit_price = Decimal("0")
        line.tax_percent = Decimal("0")
        price_line(line, client=sale.client)
        line.save(update_fields=["unit_price", "tax_percent"])
    sale.recalculate()
    sale.save()
    return sale


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

    # Post the invoice as a receivable on the billing party's ledger (once).
    party = _billing_party(sale)
    if party is not None:
        from apps.finance.ledger import post_party_entry
        from apps.finance.models import PartyLedgerEntry
        already = PartyLedgerEntry.objects.filter(
            reference_type="SALE", reference_id=sale.invoice_number,
            entry_type=PartyLedgerEntry.EntryType.INVOICE,
        ).exists()
        if not already:
            post_party_entry(
                party, entry_type=PartyLedgerEntry.EntryType.INVOICE,
                entry_date=timezone.now().date(), debit=sale.grand_total,
                reference_type="SALE", reference_id=sale.invoice_number,
                narration=f"Invoice {sale.invoice_number}",
                organization=getattr(sale, "organization", None),
            )

    _sync_payment_status(sale)
    sale.save()
    audit_services.record(AuditLog.Action.UPDATE, instance=sale, description="sale completed")
    return sale


@transaction.atomic
def add_payment(sale: Sale, *, method, amount, reference="", received_by=None, account=None):
    """Record a payment, land the money in an account, and credit the party.

    ``account`` (a finance.FinancialAccount) is optional; when given, the money
    is posted into it. If the sale is billed to a party (customer/client), a
    PAYMENT_IN credit is posted to that party's ledger.
    """
    amount = Decimal(str(amount))
    payment = Payment.objects.create(
        sale=sale, method=method, amount=amount, reference=reference,
        received_by=received_by, status=Payment.Status.PAID, account=account,
    )
    sale.amount_paid = sum((p.amount for p in sale.payments.filter(status=Payment.Status.PAID)), Decimal("0"))
    _sync_payment_status(sale)
    sale.save(update_fields=["amount_paid", "status", "updated_at"])

    if account is not None:
        from apps.finance.ledger import post_account_transaction
        from apps.finance.models import AccountTransaction
        post_account_transaction(
            account, direction=AccountTransaction.Direction.IN, amount=amount,
            occurred_at=timezone.now(), reference_type="SALE_PAYMENT",
            reference_id=sale.invoice_number, note=reference,
        )

    party = _billing_party(sale)
    if party is not None:
        from apps.finance.ledger import post_party_entry
        from apps.finance.models import PartyLedgerEntry
        post_party_entry(
            party, entry_type=PartyLedgerEntry.EntryType.PAYMENT_IN,
            entry_date=timezone.now().date(), credit=amount,
            reference_type="SALE_PAYMENT", reference_id=sale.invoice_number,
            narration=f"Payment for {sale.invoice_number}",
            organization=getattr(sale, "organization", None),
        )
    audit_services.record(
        AuditLog.Action.CREATE, instance=payment, actor=received_by, description="sale payment added"
    )
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


def next_quotation_number():
    today = timezone.now().strftime("%Y%m%d")
    from apps.pos.models import Quotation
    count = Quotation.objects.filter(quotation_number__startswith=f"QUO-{today}").count()
    return f"QUO-{today}-{count + 1:04d}"


def next_return_number():
    today = timezone.now().strftime("%Y%m%d")
    from apps.pos.models import SalesReturn
    count = SalesReturn.objects.filter(return_number__startswith=f"CRN-{today}").count()
    return f"CRN-{today}-{count + 1:04d}"


@transaction.atomic
def convert_quotation_to_sale(quotation):
    """Create a Sale from an accepted quotation (copying its priced lines)."""
    from apps.pos.models import Quotation, Sale, SaleLine

    if quotation.converted_sale_id:
        return quotation.converted_sale

    sale = Sale.objects.create(
        invoice_number=next_invoice_number(),
        customer=quotation.customer, client=quotation.client, patient=quotation.patient,
        location=quotation.location, currency="USD",
        organization=getattr(quotation, "organization", None),
    )
    for ql in quotation.lines.all():
        SaleLine.objects.create(
            sale=sale, line_type=ql.line_type, product=ql.product, lab_test=ql.lab_test,
            test_profile=ql.test_profile, billable_service=ql.billable_service,
            description=ql.description, quantity=ql.quantity, unit_price=ql.unit_price,
            discount_percent=ql.discount_percent, tax_percent=ql.tax_percent,
        )
    sale.recalculate()
    sale.save()
    quotation.converted_sale = sale
    quotation.status = Quotation.Status.CONVERTED
    quotation.save(update_fields=["converted_sale", "status", "updated_at"])
    audit_services.record(AuditLog.Action.CREATE, instance=sale, description="sale created from quotation")
    return sale


@transaction.atomic
def process_sales_return(sales_return):
    """Complete a sales return: restock the goods and credit the party.

    Restocks each product line through the inventory RETURN ledger (when
    ``restock``) and posts a CREDIT_NOTE on the billing party's ledger.
    """
    from apps.pos.models import SalesReturn

    sales_return.recalculate()
    if sales_return.restock:
        for line in sales_return.lines.all():
            if line.product_id:
                inventory_services.receive_stock(
                    product=line.product, location=sales_return.location,
                    quantity=line.quantity, reference_type="SALES_RETURN",
                    reference_id=sales_return.return_number, note="Sales return",
                )

    party = _billing_party(sales_return.sale)
    if party is not None and sales_return.total > 0:
        from apps.finance.ledger import post_party_entry
        from apps.finance.models import PartyLedgerEntry
        post_party_entry(
            party, entry_type=PartyLedgerEntry.EntryType.CREDIT_NOTE,
            entry_date=sales_return.return_date, credit=sales_return.total,
            reference_type="SALES_RETURN", reference_id=sales_return.return_number,
            narration=f"Sales return {sales_return.return_number}",
            organization=getattr(sales_return, "organization", None),
        )

    sales_return.status = SalesReturn.Status.COMPLETED
    sales_return.save(update_fields=["total", "status", "updated_at"])
    audit_services.record(
        AuditLog.Action.UPDATE, instance=sales_return, description="sales return processed"
    )
    return sales_return
