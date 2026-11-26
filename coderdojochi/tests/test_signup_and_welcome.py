from datetime import date
from unittest import mock

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from coderdojochi.factories import CDCUserFactory
from coderdojochi.forms import SCHOOL_EMAIL_WARNING
from coderdojochi.forms import SignupForm
from coderdojochi.forms import is_school_email
from coderdojochi.models import Guardian
from coderdojochi.models import Student


class SchoolEmailWarningTest(TestCase):
    # #887: warn (don't block) when someone signs up with a school address.
    def test_is_school_email(self):
        assert is_school_email("kid@cps.edu")
        assert is_school_email("Parent@CPS.EDU ")
        assert is_school_email("teacher@students.cps.edu")
        assert not is_school_email("parent@gmail.com")
        assert not is_school_email("someone@notcps.edu")
        assert not is_school_email("")

    def signup(self, email):
        form = SignupForm()
        form.cleaned_data = {"first_name": "Ada", "last_name": "Lovelace"}
        user = CDCUserFactory(email=email)
        with mock.patch("coderdojochi.forms.messages.warning") as warning:
            form.signup(request=mock.sentinel.request, user=user)
        user.refresh_from_db()
        assert user.first_name == "Ada"
        return warning

    def test_school_email_warns(self):
        warning = self.signup("ada@cps.edu")
        warning.assert_called_once_with(mock.sentinel.request, SCHOOL_EMAIL_WARNING)

    def test_personal_email_no_warning(self):
        self.signup("ada@example.com").assert_not_called()


@override_settings(SECURE_SSL_REDIRECT=False)
class WelcomeNextStepsTest(TestCase):
    # #845: after registering a student, offer "Find a class" and "Done".
    def setUp(self):
        user = CDCUserFactory(role="guardian", first_name="Pat", last_name="Parent")
        self.guardian = Guardian.objects.create(
            user=user, phone="312-555-0100", zip="60605"
        )
        self.client.force_login(user)

    def get(self):
        return self.client.get(reverse("welcome")).content.decode()

    def test_buttons_after_a_student_is_registered(self):
        Student.objects.create(
            guardian=self.guardian,
            first_name="Kid",
            last_name="Tester",
            birthday=date(2015, 1, 1),
            gender="girl",
        )
        html = self.get()
        assert f'href="{reverse("weallcode-programs")}">Find a class<' in html
        assert f'href="{reverse("account_home")}">Done<' in html

    def test_no_buttons_before_any_student(self):
        html = self.get()
        assert "Find a class" not in html
