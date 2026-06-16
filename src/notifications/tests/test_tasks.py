from unittest.mock import patch
from django.test import TestCase
from celery.exceptions import Retry
from notifications.tasks import send_telegram_notification_task


class TelegramNotificationTaskTests(TestCase):
    @patch("notifications.tasks.TelegramService.send_message")
    def test_task_success(self, mock_send_message):
        mock_send_message.return_value = True

        result = send_telegram_notification_task.apply(args=["success"])

        self.assertEqual(result.status, "SUCCESS")
        mock_send_message.assert_called_once_with("success")

    @patch("notifications.tasks.TelegramService.send_message")
    def test_task_retry_on_failure(self, mock_send_message):
        mock_send_message.return_value = False

        mock_send_message.side_effect = lambda *args, **kwargs: send_telegram_notification_task.retry(
            args=args, max_retries=1
        )

        with self.assertRaises(Retry):
            send_telegram_notification_task(text="test retry") # noqa
