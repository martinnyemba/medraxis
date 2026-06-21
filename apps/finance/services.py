"""Finance services: expenses, supplier payments and purchase bills.

Each flow posts into the money ledger (:mod:`apps.finance.ledger`) and, where a
party is involved, the party ledger -- inside one transaction -- so the books
stay consistent with the stock ledger.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.finance.ledger import post_account_transaction, post_party_entry
from apps.finance.models import (
    AccountTransaction,
    Expense,
    PartyLedgerEntry,
    SupplierPayment,
    SupplierPaymentAllocation,
)

ZERO = Decimal("0")


def _next_number(model, field, prefix):
    today = timezone.now().strftime("%Y%m%d")
    stem = f"{prefix}-{today}"
    count = model.objects.filter(**{f"{field}__startswith": stem}).count()
    return f"{stem}-{count + 1:04d}"


@transaction.atomic
def record_expense(*, category, amount, expense_date=None, account=None, supplier=None,
                   tax_amount=ZERO, payment_method="", note="", organization=None):
    """Record a business expense; debits the cash/bank account when supplied."""
    expense_date = expense_date or timezone.now().date()
    expense = Expense.objects.create(
        number=_next_number(Expense, "number", "EXP"),
        category=category, amount=Decimal(str(amount)), tax_amount=Decimal(str(tax_amount)),
        expense_date=expense_date, account=account, supplier=supplier,
        payment_method=payment_method, note=note, organization=organization,
    )
    if account is not None:
        post_account_transaction(
            account, direction=AccountTransaction.Direction.OUT, amount=expense.total,
            occurred_at=timezone.now(), reference_type="EXPENSE", reference_id=expense.number,
            note=note or category.name,
        )
    return expense


@transaction.atomic
def create_purchase_bill(*, supplier, location, items, bill_date=None, purchase_order=None,
                         supplier_invoice_no="", receive_stock=True, organization=None):
    """Create a supplier bill (payable) and optionally receive its stock.

    ``items`` is a list of dicts: product, quantity, unit_cost, tax_percent,
    batch_number, expiry_date. Posts a PURCHASE_BILL credit on the supplier
    ledger (we owe them) and, when ``receive_stock``, adds stock via the
    inventory ledger.
    """
    from apps.inventory.models import PurchaseBill, PurchaseBillItem
    from apps.inventory.services import receive_stock as receive_stock_fn

    bill = PurchaseBill.objects.create(
        bill_number=_next_number(PurchaseBill, "bill_number", "BILL"),
        supplier=supplier, location=location, purchase_order=purchase_order,
        bill_date=bill_date or timezone.now().date(),
        supplier_invoice_no=supplier_invoice_no, organization=organization,
    )
    for item in items:
        PurchaseBillItem.objects.create(
            purchase_bill=bill, product=item["product"],
            quantity=Decimal(str(item["quantity"])),
            unit_cost=Decimal(str(item.get("unit_cost", 0))),
            tax_percent=Decimal(str(item.get("tax_percent", 0))),
            batch_number=item.get("batch_number", ""),
            expiry_date=item.get("expiry_date"),
        )
        if receive_stock:
            receive_stock_fn(
                product=item["product"], location=location,
                quantity=Decimal(str(item["quantity"])),
                unit_cost=Decimal(str(item.get("unit_cost", 0))),
                batch_number=item.get("batch_number", ""),
                expiry_date=item.get("expiry_date"),
                reference_type="PURCHASE_BILL", reference_id=bill.bill_number,
            )
    bill.recalculate()
    bill.save()

    post_party_entry(
        supplier, entry_type=PartyLedgerEntry.EntryType.PURCHASE_BILL,
        entry_date=bill.bill_date, credit=bill.grand_total,
        reference_type="PURCHASE_BILL", reference_id=bill.bill_number,
        narration=f"Purchase bill {bill.bill_number}", organization=organization,
    )
    return bill


@transaction.atomic
def pay_supplier(*, supplier, amount, account=None, paid_on=None, method="CASH",
                 reference="", allocations=None, note="", organization=None):
    """Pay a supplier (money out); debits the supplier ledger and allocates to bills.

    ``allocations`` is an optional list of (purchase_bill, amount) tuples; their
    amounts must not exceed ``amount``. Allocated bills get their amount_paid and
    status updated.
    """
    amount = Decimal(str(amount))
    payment = SupplierPayment.objects.create(
        number=_next_number(SupplierPayment, "number", "SPY"),
        supplier=supplier, account=account, amount=amount,
        paid_on=paid_on or timezone.now().date(), method=method,
        reference=reference, note=note, organization=organization,
    )

    for bill, alloc_amount in (allocations or []):
        alloc_amount = Decimal(str(alloc_amount))
        SupplierPaymentAllocation.objects.create(
            payment=payment, purchase_bill=bill, amount=alloc_amount)
        bill.amount_paid += alloc_amount
        if bill.amount_paid >= bill.grand_total:
            bill.status = bill.Status.PAID
        elif bill.amount_paid > 0:
            bill.status = bill.Status.PARTIAL
        bill.save(update_fields=["amount_paid", "status"])

    if account is not None:
        post_account_transaction(
            account, direction=AccountTransaction.Direction.OUT, amount=amount,
            occurred_at=timezone.now(), reference_type="SUPPLIER_PAYMENT",
            reference_id=payment.number, note=note,
        )

    post_party_entry(
        supplier, entry_type=PartyLedgerEntry.EntryType.PAYMENT_OUT,
        entry_date=payment.paid_on, debit=amount,
        reference_type="SUPPLIER_PAYMENT", reference_id=payment.number,
        narration=f"Payment {payment.number}", organization=organization,
    )
    return payment
