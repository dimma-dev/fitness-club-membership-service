from celery import shared_task, Task
from notifications.services.telegram_service import TelegramService


@shared_task(
    bind=True,
    default_retry_delay=15,
    max_retries=3
)
def send_telegram_notification_task(self: Task, text: str):
    success = TelegramService.send_message(text)

    if not success:
        raise self.retry()
