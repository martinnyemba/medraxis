"""Auto-verification, demographic reference ranges and reflex testing.

The transparent rule engine behind "AI automation":

* :func:`resolve_reference_range` picks the most specific age/sex range.
* :func:`flag_with_reference_range` flags a result against it (falling back to
  the analyte concept's global range).
* :func:`auto_verify_result` decides whether a result may be released without a
  human, honouring range/critical gates and a delta check.
* :func:`apply_reflex` auto-orders a follow-up test on abnormality.
"""

from django.db import transaction
from django.utils import timezone

from apps.lis.models import AutoVerificationRule, LabResult, ReferenceRange


def _age_days(patient):
    person = getattr(patient, "person", None)
    if person is None or not person.birthdate:
        return None
    today = timezone.now().date()
    return (today - person.birthdate).days


def resolve_reference_range(lab_test, analyte, patient):
    """Return the best-matching ReferenceRange for a test/analyte and patient."""
    sex = None
    age_days = None
    if patient is not None and getattr(patient, "person", None):
        sex = patient.person.gender if patient.person.gender in ("M", "F") else None
        age_days = _age_days(patient)

    candidates = ReferenceRange.objects.filter(lab_test=lab_test)
    if analyte is not None:
        candidates = candidates.filter(analyte__in=[analyte, None])

    best, best_score = None, -1
    for rng in candidates:
        if rng.matches(sex=sex, age_days=age_days) and rng.specificity > best_score:
            best, best_score = rng, rng.specificity
    return best


def flag_with_reference_range(result: LabResult):
    """Deprecated alias of :func:`apps.lis.services.compute_flag`.

    Demographic reference-range flagging now lives in the single ``compute_flag``
    entry point so every channel flags consistently. Kept for backward
    compatibility with existing callers/tests.
    """
    from apps.lis.services import compute_flag

    return compute_flag(result)


def _previous_value(result: LabResult):
    """The patient's most recent released numeric value for this analyte."""
    prev = (
        LabResult.objects.filter(
            analyte=result.analyte,
            test_order__patient=result.test_order.patient_id,
            status=LabResult.Status.RELEASED,
            value_numeric__isnull=False,
        )
        .exclude(pk=result.pk)
        .order_by("-verified_at", "-id")
        .first()
    )
    return prev.value_numeric if prev else None


def delta_check_passes(result: LabResult, threshold_percent):
    """True if the result is within ``threshold_percent`` of the previous value."""
    if threshold_percent is None:
        return True
    previous = _previous_value(result)
    if previous in (None, 0) or result.value_numeric is None:
        return True
    change = abs(result.value_numeric - previous) / abs(previous) * 100
    return change <= threshold_percent


CRITICAL_FLAGS = {LabResult.Flag.CRITICAL_HIGH, LabResult.Flag.CRITICAL_LOW}
ABNORMAL_FLAGS = CRITICAL_FLAGS | {LabResult.Flag.HIGH, LabResult.Flag.LOW, LabResult.Flag.ABNORMAL}


def auto_verify_result(result: LabResult):
    """Apply the test's auto-verification rule. Returns True if auto-verified.

    System auto-verification sets status VERIFIED with no ``verified_by``
    provider (so it's distinguishable from human verification in audit).
    """
    rule = AutoVerificationRule.objects.filter(
        lab_test=result.test_order.lab_test, enabled=True
    ).first()
    if rule is None or result.status != LabResult.Status.ENTERED:
        return False

    if rule.block_on_critical and result.flag in CRITICAL_FLAGS:
        return False
    if rule.require_in_range and result.flag and result.flag != LabResult.Flag.NORMAL:
        return False
    if not delta_check_passes(result, rule.delta_check_percent):
        return False

    result.status = LabResult.Status.VERIFIED
    result.verified_at = timezone.now()
    result.save(update_fields=["status", "verified_at", "changed_at"])
    return True


@transaction.atomic
def apply_reflex(result: LabResult, *, orderer=None):
    """If the result is abnormal and a reflex test is configured, auto-order it.

    Returns the created reflex TestOrder, or None.
    """
    rule = AutoVerificationRule.objects.filter(
        lab_test=result.test_order.lab_test, enabled=True, reflex_on_abnormal__isnull=False
    ).first()
    if rule is None or result.flag not in ABNORMAL_FLAGS:
        return None

    from apps.emr.models import OrderType
    from apps.emr.services import next_order_number
    from apps.lis.models import TestOrder

    parent = result.test_order
    reflex_test = rule.reflex_on_abnormal
    # Avoid duplicate reflexes for the same parent + test.
    existing = TestOrder.objects.filter(
        previous_order=parent, lab_test=reflex_test
    ).exists()
    if existing:
        return None

    order_type = parent.order_type or OrderType.objects.filter(name="Test Order").first()
    return TestOrder.objects.create(
        order_number=next_order_number(),
        order_type=order_type,
        concept=reflex_test.concept,
        patient=parent.patient,
        encounter=parent.encounter,
        orderer=orderer or parent.orderer,
        lab_test=reflex_test,
        previous_order=parent,
        date_activated=timezone.now(),
        instructions=f"Reflex from {parent.order_number} ({result.analyte.name} abnormal).",
    )
