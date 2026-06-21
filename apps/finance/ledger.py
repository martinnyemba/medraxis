"""Party-ledger and money-account posting (append-only, balance-carrying).

Sign convention (single, consistent across party types):
``balance = cumulative(debit - credit)``.

* **balance > 0** -> the party owes us (a receivable; typical for a customer).
* **balance < 0** -> we owe the party (a payable; typical for a supplier).

So a customer invoice is a *debit*, a payment received a *credit*; a supplier
purchase bill is a *credit*, a payment made a *debit*.
"""
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.finance.models import AccountTransaction, PartyLedgerEntry

ZERO = Decimal("0")


def _party_ct(party):
    return ContentType.objects.get_for_model(party.__class__)


def party_balance(party):
    """Current running balance for a party (0 if no entries)."""
    ct = _party_ct(party)
    last = (
        PartyLedgerEntry.objects.filter(party_content_type=ct, party_object_id=party.pk)
        .order_by("-entry_date", "-id")
        .first()
    )
    return last.balance if last else ZERO


def statement(party):
    """All ledger entries for a party, oldest first (a party statement)."""
    ct = _party_ct(party)
    return PartyLedgerEntry.objects.filter(
        party_content_type=ct, party_object_id=party.pk
    ).order_by("entry_date", "id")


@transaction.atomic
def post_party_entry(party, *, entry_type, entry_date, debit=ZERO, credit=ZERO,
                     reference_type="", reference_id="", narration="", organization=None):
    """Append a ledger entry for a party and carry the running balance."""
    debit = Decimal(str(debit or 0))
    credit = Decimal(str(credit or 0))
    ct = _party_ct(party)
    previous = party_balance(party)
    balance = previous + debit - credit
    return PartyLedgerEntry.objects.create(
        party_content_type=ct,
        party_object_id=party.pk,
        organization=organization or getattr(party, "organization", None),
        entry_type=entry_type,
        entry_date=entry_date,
        debit=debit,
        credit=credit,
        balance=balance,
        reference_type=reference_type,
        reference_id=str(reference_id or ""),
        narration=narration,
    )


@transaction.atomic
def post_account_transaction(account, *, direction, amount, occurred_at,
                             reference_type="", reference_id="", note=""):
    """Move money in/out of a financial account and update its balance."""
    amount = Decimal(str(amount))
    account.refresh_from_db(fields=["current_balance"])
    if direction == AccountTransaction.Direction.IN:
        account.current_balance += amount
    else:
        account.current_balance -= amount
    account.save(update_fields=["current_balance"])

    return AccountTransaction.objects.create(
        account=account,
        direction=direction,
        amount=amount,
        balance_after=account.current_balance,
        occurred_at=occurred_at,
        reference_type=reference_type,
        reference_id=str(reference_id or ""),
        note=note,
    )
