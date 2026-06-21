"""Inventory services: the single funnel for all stock movement.

Centralising movement here guarantees the batch quantity and the ledger always
move together, inside one transaction, with FEFO (First-Expiry-First-Out)
issuing for batch-tracked products.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.inventory.models import StockBatch, StockTransaction


class InsufficientStock(Exception):
    """Raised when an issue/sale/dispense exceeds available quantity."""


@transaction.atomic
def receive_stock(*, product, location, quantity, unit_cost=Decimal("0"),
                  batch_number="", expiry_date=None, reference_type="", reference_id="", note=""):
    """Add stock into a (product, location, batch), writing a RECEIPT ledger row."""
    quantity = Decimal(str(quantity))
    batch, _ = StockBatch.objects.select_for_update().get_or_create(
        product=product, location=location, batch_number=batch_number,
        defaults={"expiry_date": expiry_date, "cost_price": unit_cost},
    )
    batch.quantity_on_hand += quantity
    if expiry_date:
        batch.expiry_date = expiry_date
    if unit_cost:
        batch.cost_price = unit_cost
    batch.save()

    return StockTransaction.objects.create(
        product=product, batch=batch, location=location,
        transaction_type=StockTransaction.TxnType.RECEIPT,
        quantity=quantity, unit_cost=unit_cost,
        reference_type=reference_type, reference_id=str(reference_id), note=note,
    )


@transaction.atomic
def issue_stock(*, product, location, quantity, transaction_type,
                reference_type="", reference_id="", note=""):
    """Remove stock using FEFO across batches; writes negative ledger rows.

    Returns the list of created :class:`StockTransaction` rows (one per batch
    touched). Raises :class:`InsufficientStock` if demand cannot be met.
    """
    quantity = Decimal(str(quantity))
    batches = list(
        StockBatch.objects.select_for_update()
        .filter(product=product, location=location, quantity_on_hand__gt=0)
        .order_by(models_expiry_order())
    )
    available = sum((b.quantity_on_hand for b in batches), Decimal("0"))
    if available < quantity:
        raise InsufficientStock(
            f"Only {available} of {product.sku} available at location {location_id(location)}; "
            f"requested {quantity}."
        )

    remaining = quantity
    txns = []
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity_on_hand, remaining)
        batch.quantity_on_hand -= take
        batch.save(update_fields=["quantity_on_hand", "updated_at"])
        txns.append(
            StockTransaction.objects.create(
                product=product, batch=batch, location=location,
                transaction_type=transaction_type, quantity=-take,
                unit_cost=batch.cost_price, reference_type=reference_type,
                reference_id=str(reference_id), note=note,
            )
        )
        remaining -= take
    return txns


def models_expiry_order():
    """FEFO: expiring batches first, then nulls last (treated as far future)."""
    from django.db.models import F

    return F("expiry_date").asc(nulls_last=True)


def location_id(location):
    return getattr(location, "pk", location)


def expiring_soon(days=90, location=None):
    """Batches expiring within ``days`` (for alerts/dashboards)."""
    cutoff = timezone.now().date() + timedelta(days=days)
    qs = StockBatch.objects.filter(
        quantity_on_hand__gt=0, expiry_date__isnull=False, expiry_date__lte=cutoff
    )
    if location is not None:
        qs = qs.filter(location=location)
    return qs.select_related("product", "location").order_by("expiry_date")
