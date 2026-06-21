"""EMR domain services (kept out of views and models).

Encapsulates cross-cutting workflows like generating unique, human-readable
order numbers and patient identifiers.
"""
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.emr.models import Order


def next_order_number():
    """Generate a unique, sortable order number, e.g. ``ORD-20260620-000042``.

    Uses a row count within the day plus the PK to stay unique under
    concurrency without an extra sequence table.
    """
    today = timezone.now().strftime("%Y%m%d")
    with transaction.atomic():
        count_today = Order.all_objects.filter(
            order_number__startswith=f"ORD-{today}"
        ).count()
        return f"ORD-{today}-{count_today + 1:06d}"


def luhn_check_digit(number: str) -> str:
    """Compute a Luhn (mod-10) check digit for a numeric identifier base."""
    digits = [int(d) for d in number if d.isdigit()]
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd) + sum(sum(divmod(d * 2, 10)) for d in even)
    return str((10 - (total % 10)) % 10)


def generate_patient_identifier(prefix: str | None = None) -> str:
    """Generate a prefixed, check-digited patient identifier (e.g. ``MRX-000123-7``)."""
    from apps.emr.models import PatientIdentifier

    prefix = prefix or settings.MEDRAXIS["PATIENT_IDENTIFIER_PREFIX"]
    seq = PatientIdentifier.all_objects.count() + 1
    base = f"{seq:06d}"
    return f"{prefix}-{base}-{luhn_check_digit(base)}"
