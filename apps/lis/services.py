"""LIS workflow services: accessioning and the result release pipeline."""
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.core.services import audit as audit_services
from apps.emr.models import Obs
from apps.lis.models import LabResult, Specimen


def next_accession_number():
    """Generate a daily-sequenced accession number, e.g. ``ACC-20260620-00042``."""
    today = timezone.now().strftime("%Y%m%d")
    count_today = Specimen.all_objects.filter(
        accession_number__startswith=f"ACC-{today}"
    ).count()
    return f"ACC-{today}-{count_today + 1:05d}"


def _flag_from_limits(value, low_normal, hi_normal, low_critical, hi_critical):
    if low_critical is not None and value <= low_critical:
        return LabResult.Flag.CRITICAL_LOW
    if hi_critical is not None and value >= hi_critical:
        return LabResult.Flag.CRITICAL_HIGH
    if low_normal is not None and value < low_normal:
        return LabResult.Flag.LOW
    if hi_normal is not None and value > hi_normal:
        return LabResult.Flag.HIGH
    return LabResult.Flag.NORMAL


def compute_flag(result: LabResult):
    """Derive a high/low/critical flag for a numeric result.

    This is the **single** flagging entry point used by every channel (manual
    entry and analyzer ingestion alike), so a result flags identically however
    it arrives. It prefers a demographic (age/sex) :class:`ReferenceRange` when
    one is configured for the test, and otherwise falls back to the analyte
    concept's global range.
    """
    value = result.value_numeric
    if value is None:
        return result.flag or ""

    # Prefer a demographic reference range (resolved by test + patient).
    rng = None
    if result.test_order_id:
        from apps.lis.automation_service import resolve_reference_range
        rng = resolve_reference_range(
            result.test_order.lab_test, result.analyte, result.test_order.patient
        )
    if rng is not None:
        if rng.text_range and not result.reference_range:
            result.reference_range = rng.text_range
        return _flag_from_limits(
            value, rng.low_normal, rng.hi_normal, rng.low_critical, rng.hi_critical
        )

    concept = result.analyte
    return _flag_from_limits(
        value, concept.low_normal, concept.hi_normal,
        concept.low_critical, concept.hi_critical,
    )


@transaction.atomic
def enter_result(result: LabResult, *, provider=None):
    """Record a result value, auto-flagging it, and mark it ENTERED."""
    result.flag = compute_flag(result)
    result.status = LabResult.Status.ENTERED
    result.entered_by = provider
    result.entered_at = timezone.now()
    result.save()
    audit_services.record(
        AuditLog.Action.UPDATE, instance=result, actor=provider, description="lab result entered"
    )
    return result


@transaction.atomic
def verify_result(result: LabResult, *, provider=None):
    """Technically verify an entered result (two-person rule enforced in views)."""
    result.status = LabResult.Status.VERIFIED
    result.verified_by = provider
    result.verified_at = timezone.now()
    result.save(update_fields=["status", "verified_by", "verified_at", "changed_at"])
    audit_services.record(
        AuditLog.Action.UPDATE, instance=result, actor=provider, description="lab result verified"
    )
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
    audit_services.record(AuditLog.Action.UPDATE, instance=result, description="lab result released")
    return result
