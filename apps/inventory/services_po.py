"""Purchase-order helpers."""
from django.utils import timezone

from apps.inventory.models import PurchaseOrder


def next_po_number():
    today = timezone.now().strftime("%Y%m%d")
    count = PurchaseOrder.objects.filter(po_number__startswith=f"PO-{today}").count()
    return f"PO-{today}-{count + 1:04d}"
