from django.test import TestCase

from coderdojochi.factories import MentorFactory
from coderdojochi.forms import MentorForm


class MentorFormPhoneTest(TestCase):
    # #896: staff need a way to reach volunteers on class day.
    def test_phone_required(self):
        form = MentorForm(data={"phone": ""}, instance=MentorFactory())
        assert not form.is_valid()
        assert "phone" in form.errors

    def test_phone_given(self):
        form = MentorForm(data={"phone": "312-555-0100"}, instance=MentorFactory())
        form.is_valid()
        assert "phone" not in form.errors
