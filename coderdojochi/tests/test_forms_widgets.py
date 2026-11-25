from django.test import TestCase

from coderdojochi.forms import GuardianForm
from coderdojochi.forms import MentorForm
from coderdojochi.forms import StudentForm


class DateWidgetTest(TestCase):
    def test_birthday_fields_render_as_html5_date(self):
        for form_class in (MentorForm, GuardianForm, StudentForm):
            with self.subTest(form=form_class.__name__):
                html = str(form_class()["birthday"])

                assert 'type="date"' in html
                assert 'name="birthday"' in html
                assert "form-control" in html

    def test_student_birthday_keeps_age_bounds(self):
        html = str(StudentForm()["birthday"])

        assert 'min="' in html
        assert 'max="' in html
