"""Local development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Show full DRF browsable API locally.
INSTALLED_APPS += []  # noqa: F405

# Console email backend for development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax throttling locally.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "user": "100000/hour",
    "anon": "1000/hour",
}

CORS_ALLOW_ALL_ORIGINS = True
