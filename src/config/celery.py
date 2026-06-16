import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Load configuration from Django settings, all celery configuration should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    "mark-expired-memberships": {
        "task": "membership.tasks.mark_expired_memberships",
        "schedule": crontab(hour=0, minute=0),
    },
    "send-expiration-reminders-7-days": {
        "task": "membership.tasks.send_expiration_reminders",
        "schedule": crontab(hour=9, minute=0),
        "kwargs": {"days_before": 7},
    },
    "auto-renew-memberships": {
        "task": "membership.tasks.auto_renew_memberships",
        "schedule": crontab(hour=1, minute=0),
    },
}