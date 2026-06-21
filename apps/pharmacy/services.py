"""Pharmacy dispensing service -- issues stock and records the event atomically."""
from django.db import transaction

from apps.inventory import services as inventory_services
from apps.inventory.models import StockTransaction
from apps.pharmacy.models import Dispense


@transaction.atomic
def dispense(*, product, location, quantity, patient=None, drug_order=None,
             provider=None, unit_price=None, note=""):
    """Dispense a product: draw down stock (FEFO) then record the event.

    Raises :class:`apps.inventory.services.InsufficientStock` if there is not
    enough on hand, rolling back cleanly.
    """
    inventory_services.issue_stock(
        product=product, location=location, quantity=quantity,
        transaction_type=StockTransaction.TxnType.DISPENSE,
        reference_type="DISPENSE",
        reference_id=str(getattr(drug_order, "pk", "") or ""),
        note=note,
    )
    if unit_price is None:
        unit_price = product.sale_price

    dispense_event = Dispense.objects.create(
        drug_order=drug_order, patient=patient, product=product, location=location,
        quantity=quantity, unit_price=unit_price, dispensed_by=provider, note=note,
    )

    # Advance the prescription's fulfilment status when fully dispensed.
    if drug_order is not None and drug_order.quantity_dispensed >= drug_order.quantity:
        drug_order.fulfiller_status = drug_order.FulfillerStatus.COMPLETED
        drug_order.save(update_fields=["fulfiller_status", "changed_at"])

    return dispense_event
