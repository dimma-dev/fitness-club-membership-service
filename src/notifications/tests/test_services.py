from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
import requests
from notifications.services.telegram_service import TelegramService


class TelegramServiceTests(TestCase):

    @patch("notifications.services.telegram_service.requests.post")
    def test_send_message_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None

        test_text = "message"
        result = TelegramService.send_message(test_text)

        self.assertTrue(result)

        expected_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        expected_payload = {
            "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
            "text": test_text,
            "parse_mode": "HTML"
        }
        mock_post.assert_called_once_with(expected_url, json=expected_payload, timeout=10)

    @patch("notifications.services.telegram_service.requests.post")
    def test_send_message_http_error(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = requests.RequestException("API Error")

        result = TelegramService.send_message("error")

        self.assertFalse(result)

    @patch("notifications.services.telegram_service.requests.post")
    def test_send_message_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Timeout error")

        result = TelegramService.send_message("timeout")

        self.assertFalse(result)
