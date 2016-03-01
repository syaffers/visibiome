from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'darp.settings')

app = Celery('darp')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

# This allows you to load tasks from app/tasks.py files, they are
# autodiscovered. Check @shared_app decorator to do that.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
