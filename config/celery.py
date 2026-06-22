"""Celery application for background task processing."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("medraxis")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "process-due-notifications": {
        "task": "apps.notifications.tasks.process_due_notifications",
        "schedule": 60.0,
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # pragma: no cover - utility
    print(f"Request: {self.request!r}")
