# CodePlatform/celery.py
import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "CodePlatform.settings"
)

app = Celery("CodePlatform")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

app.autodiscover_tasks()