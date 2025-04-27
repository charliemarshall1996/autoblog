# {{ project_name }}/celery.py
import os
from celery import Celery


# Set default django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      '{{ project_name }}.settings.base')


app = Celery('{{ project_name }}')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
