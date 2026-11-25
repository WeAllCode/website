from datetime import datetime
from datetime import timedelta
from http import HTTPStatus

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from icalendar import Calendar

from coderdojochi.factories import SessionFactory
from coderdojochi.models import Location
from coderdojochi.models import Meeting
from coderdojochi.models import MeetingType


@override_settings(SECURE_SSL_REDIRECT=False)
class CalendarViewTest(TestCase):
    def _event(self, url):
        response = self.client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"].startswith("text/calendar")
        (event,) = Calendar.from_ical(response.content).walk("VEVENT")

        dtstamp = event.decoded("dtstamp")
        assert isinstance(dtstamp, datetime)
        assert dtstamp.tzinfo is not None
        assert dtstamp.utcoffset() == timedelta(0)
        assert isinstance(event.decoded("dtstart"), datetime)
        return event

    def test_session_calendar(self):
        session = SessionFactory.create(
            course__code="PY1",
            course__title="Intro to Python",
        )

        event = self._event(reverse("session-calendar", args=[session.pk]))

        assert str(event["SUMMARY"]) == "We All Code: PY1 - Intro to Python"

    def test_meeting_calendar(self):
        start = timezone.now() + timedelta(days=7)
        meeting = Meeting.objects.create(
            meeting_type=MeetingType.objects.create(
                code="MM",
                title="Mentor meeting",
                slug="mentor-meeting",
            ),
            location=Location.objects.create(
                name="HQ",
                address="1 Main",
                city="Chicago",
                state="IL",
                zip="60601",
            ),
            start_date=start,
            end_date=start + timedelta(hours=2),
        )

        event = self._event(reverse("meeting-calendar", args=[meeting.pk]))

        assert str(event["SUMMARY"]) == "We All Code: MM - Mentor meeting"
