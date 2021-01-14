import logging

from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class SlackNotification:
    DEFAULT_PAYLOAD = {"channel": settings.SLACK_ALERTS_CHANNEL, "text": "IMPLEMENT_ME"}

    def __init__(self):
        self.payload = DEFAULT_PAYLOAD

    def send(self):
        res = requests.post(settings.SLACK_WEBHOOK_URL, json={**self.DEFAULT_PAYLOAD, **self.payload})

        if res.status_code != requests.codes.ok:
            logger.error({"msg": "Unable to send Slack notification", "error": res.content})


class NewMentorNotification(SlackNotification):
    def __init__(self, mentor):
        self.payload = {
            "blocks": [
                {"type": "divider"},
                {"type": "section", "text": {"text": "👋 New mentor signup!", "type": "mrkdwn"}},
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Name*: \n{mentor.full_name}"},
                        {"type": "mrkdwn", "text": f"*Email*: \n{mentor.email}"},
                    ],
                },
            ]
        }


class NewMentorOrderNotification(SlackNotification):
    def __init__(self, mentor_order):
        name = mentor_order.mentor.full_name
        email = mentor_order.mentor.email
        location = mentor_order.session.location.name
        start_date = mentor_order.session.start_date.strftime("%Y-%m-%d")

        self.payload = {
            "blocks": [
                {"type": "divider"},
                {"type": "section", "text": {"type": "mrkdwn", "text": "🏫 New mentor enrollment!"}},
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Name*: \n{name}\n"},
                        {"type": "mrkdwn", "text": f"*Email*: \n{email}\n"},
                        {"type": "mrkdwn", "text": f"*Location*: \n{location}"},
                        {"type": "mrkdwn", "text": f"*Date*: \n{start_date}"},
                    ],
                },
            ]
        }


class NewMentorBgCheckNotification(SlackNotification):
    def __init__(self, mentor):
        self.payload = {
            "blocks": [
                {"type": "divider"},
                {"type": "section", "text": {"type": "mrkdwn", "text": "✅ New mentor background check!"}},
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Name*: \n{mentor.user.name}"},
                        {"type": "mrkdwn", "text": f"*Email*: \n{mentor.user.email}"},
                    ],
                },
            ]
        }
