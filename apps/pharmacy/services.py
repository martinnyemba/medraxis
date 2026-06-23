"""Pharmacy services -- prescribing safety, dispensing and reversal."""
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.services import audit as audit_services
from apps.inventory import services as inventory_services
from apps.inventory.models import StockTransaction
from apps.pharmacy.models import Dispense, DispenseBatch


class DispenseReversalError(Exception):
    """Raised when a dispense cannot be reversed (already returned/cancelled)."""


def _product_allergen_concepts(product):
    """Concept ids relevant to allergy matching for a product.

    The product's clinical drug concept plus, for a combination drug, each of
    its ingredient concepts -- so an allergy to one ingredient flags a
    combination product that contains it.
    """
    ids = set()
    if product.drug_concept_id:
        ids.add(product.drug_concept_id)
    if product.drug_id:
        from apps.emr.models import DrugIngredient

        ids.update(
            DrugIngredient.objects.filter(drug_id=product.drug_id)
            .values_list("ingredient_id", flat=True)
        )
    return ids


def check_drug_allergies(patient, product):
    """Return the patient's active allergies that contraindicate this product.

    Matches at three levels, most-specific first:

    * **exact** -- the allergen concept is the product's drug concept;
    * **ingredient** -- the allergen is an ingredient of a combination product;
    * **class** -- the allergen is a drug-class concept set that *contains* one of
      the product's concepts (e.g. a "Penicillins" allergy flags amoxicillin).

    Each returned allergy carries a ``match_reason`` attribute for the UI.
    """
    if patient is None or product is None:
        return []
    concept_ids = _product_allergen_concepts(product)
    if not concept_ids:
        return []
    from apps.emr.models import Allergy, ConceptSetMembership

    allergies = list(
        Allergy.objects.filter(patient=patient, voided=False).select_related("allergen")
    )
    if not allergies:
        return []

    # Drug-class concept sets that contain any of the product's concepts.
    classes_containing = set(
        ConceptSetMembership.objects.filter(member_id__in=concept_ids)
        .values_list("concept_set_id", flat=True)
    )

    matched = []
    for a in allergies:
        if a.allergen_id == product.drug_concept_id:
            a.match_reason = "exact"
            matched.append(a)
        elif a.allergen_id in concept_ids:
            a.match_reason = "ingredient"
            matched.append(a)
        elif a.allergen_id in classes_containing:
            a.match_reason = "class"
            matched.append(a)
    return matched


@transaction.atomic
def dispense(*, product, location, quantity, patient=None, drug_order=None,
             provider=None, unit_price=None, note=""):
    """Dispense a product: draw down stock (FEFO) then record the event.

    Raises :class:`apps.inventory.services.InsufficientStock` if there is not
    enough on hand, rolling back cleanly.
    """
    txns = inventory_services.issue_stock(
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
    # Record which batch(es) FEFO drew from, for traceability and exact reversal.
    for t in txns:
        DispenseBatch.objects.create(
            dispense=dispense_event, batch=t.batch,
            quantity=-t.quantity, unit_cost=t.unit_cost,
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
def record_pos_dispense(*, sale, product, location, quantity, unit_price, txns,
                        patient=None, provider=None):
    """Record a clinical dispense for a medicine sold over the counter at POS.

    The stock has *already* moved as the sale's ledger row, so this does **not**
    issue stock again -- it creates the dispensing record (with batch
    traceability copied from ``txns``) so controlled/medicinal products that
    leave via the till are auditable. Reversal is via the sales-return flow.
    """
    event = Dispense.objects.create(
        sale=sale, patient=patient, product=product, location=location,
        quantity=quantity, unit_price=unit_price, dispensed_by=provider,
        note=f"POS sale {sale.invoice_number}",
    )
    for t in txns:
        DispenseBatch.objects.create(
            dispense=event, batch=t.batch, quantity=-t.quantity, unit_cost=t.unit_cost,
        )
    audit_services.record(
        AuditLog.Action.CREATE, instance=event, actor=provider,
        description=f"OTC dispense {quantity} {product.sku} via {sale.invoice_number}",
    )
    return event


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
    if dispense.sale_id:
        raise DispenseReversalError(
            "This dispense was made through a POS sale; reverse it with a sales return."
        )

    batch_lines = list(dispense.batch_lines.select_related("batch"))
    if batch_lines:
        # Restock each originating batch exactly (traceable reversal).
        for line in batch_lines:
            inventory_services.return_to_stock(
                product=dispense.product, location=dispense.location, quantity=line.quantity,
                unit_cost=line.unit_cost, batch_number=line.batch.batch_number,
                expiry_date=line.batch.expiry_date, reference_type="DISPENSE_RETURN",
                reference_id=str(dispense.pk), note=note or "Dispense reversed",
            )
    else:
        # Legacy dispenses without batch lines: restock to the default batch.
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
