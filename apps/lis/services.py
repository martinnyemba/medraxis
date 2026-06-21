"""LIS workflow services: accessioning and the result release pipeline."""
from django.db import transaction
from django.utils import timezone

from apps.emr.models import Obs
from apps.lis.models import LabResult, Specimen


def next_accession_number():
    """Generate a daily-sequenced accession number, e.g. ``ACC-20260620-00042``."""
    today = timezone.now().strftime("%Y%m%d")
    count_today = Specimen.all_objects.filter(
        accession_number__startswith=f"ACC-{today}"
    ).count()
    return f"ACC-{today}-{count_today + 1:05d}"


def compute_flag(result: LabResult):
    """Derive a high/low/critical flag from the analyte's reference ranges."""
    value = result.value_numeric
    if value is None:
        return ""
    concept = result.analyte
    if concept.low_critical is not None and value <= concept.low_critical:
        return LabResult.Flag.CRITICAL_LOW
    if concept.hi_critical is not None and value >= concept.hi_critical:
        return LabResult.Flag.CRITICAL_HIGH
    if concept.low_normal is not None and value < concept.low_normal:
        return LabResult.Flag.LOW
    if concept.hi_normal is not None and value > concept.hi_normal:
        return LabResult.Flag.HIGH
    return LabResult.Flag.NORMAL


@transaction.atomic
def enter_result(result: LabResult, *, provider=None):
    """Record a result value, auto-flagging it, and mark it ENTERED."""
    result.flag = compute_flag(result)
    result.status = LabResult.Status.ENTERED
    result.entered_by = provider
    result.entered_at = timezone.now()
    result.save()
    return result


@transaction.atomic
def verify_result(result: LabResult, *, provider=None):
    """Technically verify an entered result (two-person rule enforced in views)."""
    result.status = LabResult.Status.VERIFIED
    result.verified_by = provider
    result.verified_at = timezone.now()
    result.save(update_fields=["status", "verified_by", "verified_at", "changed_at"])
    return result


@transaction.atomic
def release_result(result: LabResult):
    """Release a verified result to the patient chart by creating an EMR Obs."""
    order = result.test_order
    obs = Obs.objects.create(
        person=order.patient.person,
        concept=result.analyte,
        encounter=order.encounter,
        order=order,
        obs_datetime=timezone.now(),
        value_numeric=result.value_numeric,
        value_text=result.value_text,
        value_coded=result.value_coded,
        interpretation=result.flag,
        comments=result.reference_range,
        status="FINAL",
    )
    result.obs = obs
    result.status = LabResult.Status.RELEASED
    result.save(update_fields=["obs", "status", "changed_at"])

    # Advance the order's fulfilment status.
    order.fulfiller_status = order.FulfillerStatus.COMPLETED
    order.save(update_fields=["fulfiller_status", "changed_at"])
    return result
