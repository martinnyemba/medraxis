"""Provider webhook receiver.

Endpoint: ``POST /payments/webhooks/<gateway_id>/`` -- providers are
unauthenticated to us, so this is AllowAny but **signature-gated** inside
``services.process_webhook`` (invalid signatures are recorded and ignored).
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments import services
from apps.payments.models import PaymentGateway


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, gateway_id):
        gateway = PaymentGateway.objects.filter(pk=gateway_id, is_active=True).first()
        if gateway is None:
            return Response({"detail": "Unknown gateway."}, status=404)

        event = services.process_webhook(gateway, request)
        if not event.signature_valid:
            # Acknowledge with 400 so providers surface the signature problem,
            # but we have already stored the event for audit.
            return Response({"detail": "Invalid signature."}, status=400)
        return Response({"received": True, "processed": event.processed})
