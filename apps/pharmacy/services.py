"""Pharmacy services -- prescribing safety, dispensing and reversal."""
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.services import audit as audit_services
from apps.inventory import services as inventory_services
from apps.inventory.models import StockTransaction
from apps.pharmacy.models import Dispense


class DispenseReversalError(Exception):
    """Raised when a dispense cannot be reversed (already returned/cancelled)."""


def check_drug_allergies(patient, product):
    """Return the patient's active drug allergies that match this product.

    A match is an active (non-voided) DRUG-category allergy whose allergen
    concept is the product's clinical drug concept. This is the implementable,
    deterministic core of allergy-aware prescribing: it surfaces a documented
    allergy to the very drug being prescribed so the prescriber can confirm or
    choose an alternative.
    """
    if patient is None or product is None or product.drug_concept_id is None:
        return []
    from apps.emr.models import Allergy

    return list(
        Allergy.objects.filter(
            patient=patient,
            allergen_id=product.drug_concept_id,
            voided=False,
        ).select_related("allergen")
    )


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

    audit_services.record(
        AuditLog.Action.CREATE, instance=dispense_event, actor=provider,
        description=f"dispensed {quantity} {product.sku}",
    )
    return dispense_event


@transaction.atomic
def reverse_dispense(dispense, *, provider=None, note=""):
    """Reverse a dispense: return the stock and mark the event RETURNED.

    Restocks the dispensed quantity through the inventory RETURN ledger and, if
    the linked prescription was completed by this dispense, reopens it.
    """
    if dispense.status != Dispense.Status.DISPENSED:
        raise DispenseReversalError(
            f"Dispense is {dispense.get_status_display()}; only a dispensed item can be returned."
        )

    inventory_services.return_to_stock(
        product=dispense.product, location=dispense.location, quantity=dispense.quantity,
        unit_cost=dispense.unit_price, reference_type="DISPENSE_RETURN",
        reference_id=str(dispense.pk), note=note or "Dispense reversed",
    )
    dispense.status = Dispense.Status.RETURNED
    dispense.save(update_fields=["status"])

    drug_order = dispense.drug_order
    if drug_order is not None and drug_order.fulfiller_status == drug_order.FulfillerStatus.COMPLETED:
        drug_order.fulfiller_status = drug_order.FulfillerStatus.IN_PROGRESS
        drug_order.save(update_fields=["fulfiller_status", "changed_at"])

    audit_services.record(
        AuditLog.Action.UPDATE, instance=dispense, actor=provider,
        description=f"reversed dispense of {dispense.quantity} {dispense.product.sku}",
    )
    return dispense
