"""Event-driven notifications.

Kept intentionally lean: handlers detect an event and delegate to the
notification service (which enqueues async delivery). No heavy work runs in the
signal itself.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.lis.models import LabResult


@receiver(post_save, sender=LabResult, dispatch_uid="notify_critical_result")
def notify_on_critical_result(sender, instance, **kwargs):
    """Alert the ordering provider when a released result is critical."""
    critical = {LabResult.Flag.CRITICAL_HIGH, LabResult.Flag.CRITICAL_LOW}
    if instance.status != LabResult.Status.RELEASED or instance.flag not in critical:
        return

    orderer = getattr(instance.test_order, "orderer", None)
    recipient_user = getattr(orderer, "user", None)
    if recipient_user is None:
        return

    from apps.notifications.services import queue_notification

    queue_notification(
        channel="in_app",
        subject="Critical lab result",
        body=(
            f"Critical result for order {instance.test_order.order_number}: "
            f"{instance.analyte.name} = {instance.value_numeric} ({instance.get_flag_display()})."
        ),
        recipient_user=recipient_user,
        organization=getattr(instance.test_order, "organization", None),
        dedupe_key=f"critical-result-{instance.pk}",
    )
