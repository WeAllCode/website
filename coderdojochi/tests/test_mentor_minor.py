from datetime import timedelta

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import MentorFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.forms import MentorForm
from coderdojochi.models import MentorOrder


def years_ago(years):
    today = timezone.localdate()
    return today.replace(year=today.year - years) - timedelta(days=1)


class MentorBackgroundCheckAgeTest(TestCase):
    # #553: volunteers under 18 can't get a background check, so don't require one.
    def test_minor_does_not_need_a_background_check(self):
        mentor = MentorFactory(birthday=years_ago(16), background_check=False)
        assert mentor.is_minor
        assert not mentor.needs_background_check

    def test_adult_needs_a_background_check(self):
        mentor = MentorFactory(birthday=years_ago(18), background_check=False)
        assert not mentor.is_minor
        assert mentor.needs_background_check

    def test_no_birthday_needs_a_background_check(self):
        mentor = MentorFactory(birthday=None, background_check=False)
        assert mentor.needs_background_check


@override_settings(SECURE_SSL_REDIRECT=False)
class MinorMentorSignUpTest(TestCase):
    def sign_up(self, birthday):
        mentor = MentorFactory(
            user=CDCUserFactory(role="mentor"),
            birthday=birthday,
            background_check=False,
        )
        session = SessionFactory(start_date=timezone.now() + timedelta(days=7))
        self.client.force_login(mentor.user)
        self.client.post(reverse("session-sign-up", args=[session.pk]))
        return MentorOrder.objects.filter(mentor=mentor, session=session).exists()

    def test_minor_can_sign_up_without_a_background_check(self):
        assert self.sign_up(years_ago(16))

    def test_adult_cannot_sign_up_without_a_background_check(self):
        assert not self.sign_up(years_ago(30))


class MentorZipTest(TestCase):
    # #749: a zip code, not a home address.
    def errors(self, zip_code):
        form = MentorForm(data={"zip": zip_code}, instance=MentorFactory())
        form.is_valid()
        return form.errors

    def test_zip_replaces_home_address(self):
        fields = MentorForm().fields
        assert "zip" in fields
        assert "home_address" not in fields
        assert fields["zip"].required is False

    def test_valid_zips(self):
        for zip_code in ["60601", "60601-1234", ""]:
            assert "zip" not in self.errors(zip_code), zip_code

    def test_invalid_zips(self):
        for zip_code in ["6060", "606011", "abcde", "1 Main St"]:
            assert "zip" in self.errors(zip_code), zip_code
