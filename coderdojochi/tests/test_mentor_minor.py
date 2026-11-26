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
    # #553: volunteers under 18 can't get a background check, so staff waive it.
    def test_waived_minor_does_not_need_a_background_check(self):
        mentor = MentorFactory(
            birthday=years_ago(16),
            background_check=False,
            background_check_waived=True,
        )
        assert mentor.is_minor
        assert not mentor.needs_background_check

    def test_self_reported_minor_still_needs_staff_waiver(self):
        # Mentors edit their own birthday, so age alone must not skip the check.
        mentor = MentorFactory(birthday=years_ago(16), background_check=False)
        assert mentor.needs_background_check
        assert mentor.awaiting_minor_waiver

    def test_waiver_ends_at_18(self):
        mentor = MentorFactory(
            birthday=years_ago(18),
            background_check=False,
            background_check_waived=True,
        )
        assert mentor.needs_background_check
        assert not mentor.awaiting_minor_waiver

    def test_adult_needs_a_background_check(self):
        mentor = MentorFactory(birthday=years_ago(18), background_check=False)
        assert not mentor.is_minor
        assert mentor.needs_background_check

    def test_no_birthday_needs_a_background_check(self):
        mentor = MentorFactory(birthday=None, background_check=False)
        assert mentor.needs_background_check


@override_settings(SECURE_SSL_REDIRECT=False)
class MinorMentorSignUpTest(TestCase):
    def sign_up(self, birthday, *, waived=False):
        mentor = MentorFactory(
            user=CDCUserFactory(role="mentor"),
            birthday=birthday,
            background_check=False,
            background_check_waived=waived,
        )
        session = SessionFactory(start_date=timezone.now() + timedelta(days=7))
        self.client.force_login(mentor.user)
        self.client.post(reverse("session-sign-up", args=[session.pk]))
        return MentorOrder.objects.filter(mentor=mentor, session=session).exists()

    def test_waived_minor_can_sign_up_without_a_background_check(self):
        assert self.sign_up(years_ago(16), waived=True)

    def test_unwaived_minor_cannot_sign_up(self):
        assert not self.sign_up(years_ago(16))

    def test_waiver_does_not_cover_an_adult(self):
        assert not self.sign_up(years_ago(30), waived=True)

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
