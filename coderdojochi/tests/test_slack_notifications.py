from unittest import mock

import requests
from django.test import SimpleTestCase
from django.test import override_settings

from coderdojochi.notifications import SlackNotification

WEBHOOK_URL = "https://hooks.slack.com/services/T000/B000/XXXX"
EXPECTED_TIMEOUT = 5


class SlackNotificationSendTest(SimpleTestCase):
    @override_settings(SLACK_WEBHOOK_URL="")
    @mock.patch("coderdojochi.notifications.requests.post")
    def test_skips_post_when_webhook_url_empty(self, mock_post):
        SlackNotification().send()

        mock_post.assert_not_called()

    @override_settings(SLACK_WEBHOOK_URL=WEBHOOK_URL)
    @mock.patch(
        "coderdojochi.notifications.requests.post",
        side_effect=requests.ConnectionError("no route to host"),
    )
    def test_swallows_connection_error(self, mock_post):
        with self.assertLogs("coderdojochi.notifications", level="ERROR"):
            SlackNotification().send()

        mock_post.assert_called_once()

    @override_settings(SLACK_WEBHOOK_URL=WEBHOOK_URL)
    @mock.patch("coderdojochi.notifications.requests.post")
    def test_posts_with_timeout(self, mock_post):
        mock_post.return_value = mock.Mock(status_code=200)

        SlackNotification().send()

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == WEBHOOK_URL
        assert kwargs["timeout"] == EXPECTED_TIMEOUT
