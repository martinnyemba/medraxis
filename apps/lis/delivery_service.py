"""Report dispatch: send a test order's report over WhatsApp/SMS/email/portal.

Creates a :class:`ReportDelivery` record and enqueues an actual message through
the async notifications subsystem, so retries and provider integration are
shared with the rest of the platform.
"""
from django.utils import timezone

from apps.lis.models import ReportDelivery
from apps.notifications.services import queue_notification


def _recipient_address(test_order, recipient_type, explicit):
    if explicit:
        return explicit
    if recipient_type == ReportDelivery.Recipient.REFERRER and test_order.referring_doctor_id:
        rd = test_order.referring_doctor
        return rd.phone or rd.email
    if recipient_type == ReportDelivery.Recipient.CLIENT and test_order.client_id:
        cl = test_order.client
        return cl.phone or cl.email
    # Default: the patient's phone (from a Phone person attribute) or fallback.
    patient = test_order.patient
    attr = patient.person.attributes.filter(
        attribute_type__name__icontains="phone"
    ).first()
    return attr.value if attr else ""


def dispatch_report(test_order, *, channel=ReportDelivery.Channel.WHATSAPP,
                    recipient_type=ReportDelivery.Recipient.PATIENT,
                    recipient_address="", body=""):
    """Dispatch a report and track the delivery. Returns the ReportDelivery."""
    address = _recipient_address(test_order, recipient_type, recipient_address)
    delivery = ReportDelivery.objects.create(
        test_order=test_order,
        channel=channel,
        recipient_type=recipient_type,
        recipient_address=address,
    )

    if not address:
        delivery.status = ReportDelivery.Status.FAILED
        delivery.error = "No recipient address resolved."
        delivery.save(update_fields=["status", "error"])
        return delivery

    body = body or (
        f"Your lab report for order {test_order.order_number} is ready. "
        f"Test: {test_order.lab_test.name}."
    )
    # The portal channel needs no external send; others go through notifications.
    if channel == ReportDelivery.Channel.PORTAL:
        delivery.status = ReportDelivery.Status.DELIVERED
        delivery.sent_at = timezone.now()
        delivery.save(update_fields=["status", "sent_at"])
        return delivery

    notification, _ = queue_notification(
        channel=channel,
        subject=f"Lab report {test_order.order_number}",
        body=body,
        recipient_address=address,
        organization=getattr(test_order, "organization", None),
        dedupe_key=f"report-delivery-{test_order.pk}-{channel}-{recipient_type}",
    )
    delivery.notification = notification
    delivery.status = ReportDelivery.Status.SENT
    delivery.sent_at = timezone.now()
    delivery.save(update_fields=["notification", "status", "sent_at"])
    return delivery
