"""Payment webhook URLs, mounted at ``/payments/``."""
from django.urls import path

from apps.payments.webhooks import PaymentWebhookView

app_name = "payments"

urlpatterns = [
    path("webhooks/<int:gateway_id>/", PaymentWebhookView.as_view(), name="webhook"),
]
