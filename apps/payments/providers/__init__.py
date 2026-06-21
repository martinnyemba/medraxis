"""Provider registry -- resolve an adapter for a gateway."""
from apps.payments.providers.base import PaymentError, PaymentProvider
from apps.payments.providers.flutterwave import FlutterwaveProvider
from apps.payments.providers.lenco import LencoProvider
from apps.payments.providers.manual import ManualProvider
from apps.payments.providers.stripe import StripeProvider

_REGISTRY = {
    "stripe": StripeProvider,
    "flutterwave": FlutterwaveProvider,
    "lenco": LencoProvider,
    "manual": ManualProvider,
}


def get_provider(gateway) -> PaymentProvider:
    cls = _REGISTRY.get(gateway.provider)
    if cls is None:
        raise PaymentError(f"No adapter for provider '{gateway.provider}'.")
    return cls(gateway)


__all__ = ["get_provider", "PaymentProvider", "PaymentError"]
