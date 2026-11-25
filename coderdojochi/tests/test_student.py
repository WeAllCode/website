from datetime import date

from django.test import SimpleTestCase
from django.test import TestCase
from django.utils import timezone

from coderdojochi.admin import StudentResource
from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import Order
from coderdojochi.models import Student
from weallcode.views.sitemap import StaticSitemapView

IMPORT_ROW = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "guardian_email": "parent@example.com",
    "birthday": "03/04/2015",
    "gender": "female",
    "school_name": "Hull",
    "school_type": "public",
    "photo_release": "yes",
    "consent": "yes",
}


def _guardian(email="parent@example.com"):
    return Guardian.objects.create(user=CDCUserFactory(email=email))


def _student(guardian):
    return Student.objects.create(
        guardian=guardian,
        first_name="Ada",
        last_name="Lovelace",
        birthday=date(2015, 3, 4),
        gender="female",
    )


class IsRegisteredForSessionTest(TestCase):
    def setUp(self):
        self.guardian = _guardian()
        self.student = _student(self.guardian)
        self.session = SessionFactory()

    def _order(self, **kwargs):
        return Order.objects.create(
            guardian=self.guardian,
            student=self.student,
            session=self.session,
            **kwargs,
        )

    def test_active_order_is_registered(self):
        self._order()

        assert self.student.is_registered_for_session(self.session) is True

    def test_no_order_is_not_registered(self):
        assert self.student.is_registered_for_session(self.session) is False

    def test_inactive_order_is_not_registered(self):
        self._order(is_active=False)

        assert self.student.is_registered_for_session(self.session) is False

    def test_other_session_is_not_registered(self):
        self._order()

        assert self.student.is_registered_for_session(SessionFactory()) is False


class StudentImportTest(TestCase):
    def test_birthday_is_parsed_as_date(self):
        _guardian()
        student = Student()

        StudentResource().import_obj(student, dict(IMPORT_ROW), dry_run=True)

        assert student.birthday == date(2015, 3, 4)
        assert type(student.birthday) is date

    def test_empty_birthday_raises_value_error(self):
        with self.assertRaises(ValueError):  # noqa: PT027
            StudentResource().import_obj(
                Student(),
                {**IMPORT_ROW, "birthday": ""},
                dry_run=True,
            )


class StaticSitemapTest(SimpleTestCase):
    def test_lastmod_is_timezone_aware(self):
        lastmod = StaticSitemapView().lastmod("weallcode-home")

        assert timezone.is_aware(lastmod)
