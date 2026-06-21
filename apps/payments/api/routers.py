from apps.payments.api.views import PaymentGatewayViewSet, PaymentIntentViewSet


def register_routes(router):
    router.register("payments/gateways", PaymentGatewayViewSet, basename="payment-gateway")
    router.register("payments/intents", PaymentIntentViewSet, basename="payment-intent")
