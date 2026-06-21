from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core / Platform"

    def ready(self):
        # Register cross-cutting signal handlers.
        from apps.core import signals  # noqa: F401
