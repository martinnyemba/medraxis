"""Project package initialization.

Expose the Celery app so that shared_task autodiscovery works when Celery is
installed. The import is guarded so the project still runs in environments
where Celery is intentionally absent.
"""
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:  # pragma: no cover - Celery optional at runtime
    __all__ = ()
