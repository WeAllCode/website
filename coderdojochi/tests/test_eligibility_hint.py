import re
from datetime import date
from datetime import timedelta
from html.parser import HTMLParser

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import Order
from coderdojochi.models import Student
from coderdojochi.templatetags.coderdojochi_extras import student_register_link

PAYLOAD = "{{ 1|add:1 }}<script>alert(1)</script>"


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def find(self, **attrs):
        return [
            (tag, a)
            for tag, a in self.tags
            if all(a.get(k) == v for k, v in attrs.items())
        ]


@override_settings(SECURE_SSL_REDIRECT=False)
class EligibilityHintTest(TestCase):
    def setUp(self):
        self.user = CDCUserFactory(role="guardian")
        self.guardian = Guardian.objects.create(user=self.user)
        self.session = SessionFactory(
            start_date=timezone.now() + timedelta(days=7),
            override_minimum_age_limitation=8,
            override_maximum_age_limitation=12,
            gender_limitation="female",
        )

    def student(self, gender, age):
        return Student.objects.create(
            guardian=self.guardian,
            first_name="Kid",
            last_name="Tester",
            birthday=date(timezone.now().year - age, 1, 1),
            gender=gender,
        )

    def assert_hint(self, html, *, text):
        tags = Tags(html)
        triggers = [a for tag, a in tags.tags if "interestfor" in a]
        assert len(triggers) == 1
        trigger = triggers[0]
        assert trigger["type"] == "button"
        hints = tags.find(id=trigger["interestfor"])
        assert len(hints) == 1
        assert hints[0][1]["role"] == "tooltip"
        assert hints[0][1]["popover"] == "hint"
        assert trigger["aria-describedby"] == trigger["interestfor"]
        assert text in html

    def test_age_and_gender_branch(self):
        html = student_register_link(self.student("boy", 30), self.session)
        self.assert_hint(html, text="Limited event.")

    def test_age_branch(self):
        html = student_register_link(self.student("girl", 30), self.session)
        self.assert_hint(html, text="Age-limited event.")

    def test_gender_branch(self):
        html = student_register_link(self.student("boy", 10), self.session)
        self.assert_hint(html, text="Girls-only event.")

    def test_session_fields_are_escaped_and_never_parsed_as_a_template(self):
        self.session.gender_limitation = PAYLOAD
        html = student_register_link(self.student("boy", 10), self.session)
        assert "{{ 1|add:1 }}" in html
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert not re.search(r"limited to 2", html)

    def test_href_is_quoted(self):
        student = self.student("girl", 10)
        url = reverse(
            "session-sign-up",
            kwargs={"pk": self.session.pk, "student_id": student.pk},
        )
        html = student_register_link(student, self.session)
        assert f'<a href="{url}" class="cta cta-small">Enroll</a>' == html

        Order.objects.create(
            guardian=self.guardian,
            session=self.session,
            student=student,
        )
        html = student_register_link(student, self.session)
        assert f'href="{url}"' in html
        assert "Can't make it" in html
