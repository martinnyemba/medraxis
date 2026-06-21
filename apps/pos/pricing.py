"""Unified price resolution -- the single source of truth for billing.

A POS line can bill a product, a lab test, a lab profile or a billable service.
Each has its own list price, and a B2B :class:`~apps.lis.models.Client` may have
a negotiated rate card (``PriceList``/``PriceListItem``). This module resolves
*one* unit price (and the applicable tax %) for any billable item, honouring the
client's price list first, so the "one bill" promise holds across the platform.

Precedence for a lab test:
    client price-list item  >  default price-list item  >  LabTest.price
Other items use their own list price. Resolution never raises; it falls back to
the item's base price (or zero) so billing always proceeds.
"""
from decimal import Decimal

from apps.pos.models import SaleLine

ZERO = Decimal("0")


def _client_test_price(client, lab_test):
    """Return a lab test's price from the client's active price list, or None."""
    if client is None or lab_test is None:
        return None
    from django.db.models import Q
    from django.utils import timezone
    from apps.lis.models import PriceListItem

    today = timezone.now().date()
    item = (
        PriceListItem.objects.filter(price_list__client=client, lab_test=lab_test)
        .filter(Q(price_list__valid_from__isnull=True) | Q(price_list__valid_from__lte=today))
        .filter(Q(price_list__valid_to__isnull=True) | Q(price_list__valid_to__gte=today))
        .order_by("-price_list__is_default", "-id")
        .first()
    )
    return item.price if item else None


def _default_test_price(lab_test):
    """A lab test's price from a non-client default price list, or None."""
    if lab_test is None:
        return None
    from apps.lis.models import PriceListItem

    item = (
        PriceListItem.objects.filter(
            price_list__client__isnull=True, price_list__is_default=True, lab_test=lab_test
        )
        .order_by("-id")
        .first()
    )
    return item.price if item else None


def resolve_unit_price(*, line_type, product=None, lab_test=None, test_profile=None,
                       billable_service=None, client=None):
    """Resolve the unit price for a billable item. Returns a Decimal."""
    if line_type == SaleLine.LineType.PRODUCT and product is not None:
        return product.sale_price or ZERO

    if line_type == SaleLine.LineType.LAB_TEST and lab_test is not None:
        price = _client_test_price(client, lab_test)
        if price is None:
            price = _default_test_price(lab_test)
        if price is None:
            price = lab_test.price
        return price or ZERO

    if line_type == SaleLine.LineType.LAB_PROFILE and test_profile is not None:
        return test_profile.price or ZERO

    if line_type in (SaleLine.LineType.SERVICE, SaleLine.LineType.CONSULTATION) \
            and billable_service is not None:
        return billable_service.price or ZERO

    return ZERO


def resolve_tax_percent(*, line_type, product=None, billable_service=None):
    """Resolve the applicable tax percentage for a billable item, or 0."""
    rate = None
    if line_type == SaleLine.LineType.PRODUCT and product is not None:
        rate = product.tax_rate
    elif line_type in (SaleLine.LineType.SERVICE, SaleLine.LineType.CONSULTATION) \
            and billable_service is not None:
        rate = billable_service.tax_rate
    return rate.rate_percent if rate is not None else ZERO


def price_line(line: SaleLine, *, client=None):
    """Populate a SaleLine's ``unit_price``/``tax_percent`` from catalogue prices.

    Only fills values the caller left unset (price 0 and tax 0), so an explicit
    override on the line is always respected. Mutates and returns the line
    (does not save).
    """
    if not line.unit_price:
        line.unit_price = resolve_unit_price(
            line_type=line.line_type, product=line.product, lab_test=line.lab_test,
            test_profile=line.test_profile, billable_service=line.billable_service,
            client=client,
        )
    if not line.tax_percent:
        line.tax_percent = resolve_tax_percent(
            line_type=line.line_type, product=line.product,
            billable_service=line.billable_service,
        )
    return line
