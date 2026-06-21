"""Analyzer message ingestion: parse a transmission and record lab results.

Flow: pick a protocol driver -> parse to normalised ``ResultMessage`` records ->
match each to an open test order via the specimen accession number and analyte
code -> create/update a :class:`~apps.lis.models.LabResult` in the ENTERED state
(auto-flagged). Verification and release remain human steps (two-person rule).

Matching is intentionally forgiving: an analyte code may match the order's
``LabTest.test_code``, an analyte concept's short name, or a terminology mapping
code (e.g. LOINC). Unmatched results are logged, never silently dropped.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.lis import services
from apps.lis.drivers.astm import get_driver
from apps.lis.models import AnalyzerMessage, LabResult, Specimen


def _match_analyte(test_order, code):
    """Find the analyte concept on this order's test that matches ``code``."""
    code_norm = (code or "").strip().lower()
    lab_test = test_order.lab_test

    # Single-analyte test whose code matches directly.
    if (lab_test.test_code or "").strip().lower() == code_norm:
        return lab_test.concept
    if (lab_test.loinc_code or "").strip().lower() == code_norm:
        return lab_test.concept

    for analyte in lab_test.analytes.all():
        if (analyte.short_name or "").strip().lower() == code_norm:
            return analyte
        if analyte.name.strip().lower() == code_norm:
            return analyte
        if analyte.mappings.filter(reference_term__code__iexact=code).exists():
            return analyte
    return None


def _record_result(test_order, analyte, msg, analyzer):
    """Create or update the LabResult for this order/analyte and enter it."""
    result = LabResult.objects.filter(
        test_order=test_order, analyte=analyte
    ).exclude(status=LabResult.Status.RELEASED).first()
    if result is None:
        result = LabResult(test_order=test_order, analyte=analyte)

    numeric = msg.numeric_value
    if numeric is not None:
        result.value_numeric = numeric
    else:
        result.value_text = msg.value
    result.units = msg.units or result.units
    result.reference_range = msg.reference_range or result.reference_range
    result.analyzer = analyzer
    # services.enter_result records the result in the ENTERED state. We override
    # its flag with the demographic reference-range evaluation when available.
    services.enter_result(result, provider=None)
    from apps.lis.automation_service import (
        apply_reflex,
        auto_verify_result,
        flag_with_reference_range,
    )
    demographic_flag = flag_with_reference_range(result)
    if demographic_flag != result.flag or (result.reference_range and not msg.reference_range):
        result.flag = demographic_flag
        result.save(update_fields=["flag", "reference_range"])
    # If the analyzer asserted a flag and we derived none, trust the instrument.
    if msg.flag and not result.flag:
        result.flag = msg.flag
        result.save(update_fields=["flag"])
    # "AI automation": auto-verify in-range, delta-stable results and fire reflex
    # orders on abnormality (both no-ops unless rules are configured).
    auto_verify_result(result)
    apply_reflex(result)
    return result


@transaction.atomic
def ingest_message(raw_payload, *, protocol="HL7", analyzer=None):
    """Parse and persist one analyzer transmission. Returns the AnalyzerMessage."""
    message = AnalyzerMessage.objects.create(
        analyzer=analyzer,
        protocol=protocol,
        raw_payload=raw_payload,
        status=AnalyzerMessage.Status.RECEIVED,
    )

    driver = get_driver(protocol)
    parsed = driver.parse(raw_payload)

    log = list(parsed.errors)
    matched = 0
    unmatched = 0

    for result_msg in parsed.results:
        specimen = Specimen.objects.filter(
            accession_number=result_msg.specimen_id
        ).first() if result_msg.specimen_id else None

        if specimen is None:
            unmatched += 1
            log.append(f"No specimen for accession '{result_msg.specimen_id}' "
                       f"(test {result_msg.test_code}).")
            continue

        recorded = False
        for test_order in specimen.orders.select_related("lab_test").all():
            analyte = _match_analyte(test_order, result_msg.test_code)
            if analyte is not None:
                _record_result(test_order, analyte, result_msg, analyzer)
                matched += 1
                recorded = True
                break
        if not recorded:
            unmatched += 1
            log.append(f"No matching order/analyte for test '{result_msg.test_code}' "
                       f"on specimen '{result_msg.specimen_id}'.")

    if matched and unmatched:
        message.status = AnalyzerMessage.Status.PARTIAL
    elif matched:
        message.status = AnalyzerMessage.Status.PROCESSED
    else:
        message.status = AnalyzerMessage.Status.FAILED

    message.results_matched = matched
    message.results_unmatched = unmatched
    message.log = log
    message.save(update_fields=["status", "results_matched", "results_unmatched", "log"])
    return message
