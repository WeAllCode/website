from datetime import date

import tablib
from django.contrib.auth import get_user_model
from django.test import TestCase

from coderdojochi.admin import GuardianImportResource
from coderdojochi.admin import StudentResource
from coderdojochi.models import Guardian
from coderdojochi.models import Student

User = get_user_model()

GUARDIAN_HEADERS = ["first_name", "last_name", "email", "phone", "zip"]
GUARDIAN_ROW = ["Pat", "Parent", "pat@example.com", "312-555-0100", "60605"]

STUDENT_HEADERS = [
    "first_name",
    "last_name",
    "guardian_email",
    "birthday",
    "gender",
    "school_name",
    "school_type",
    "photo_release",
    "consent",
]
STUDENT_ROW = [
    "Sam",
    "Student",
    "pat@example.com",
    "01/15/2015",
    "female",
    "Jones Elementary",
    "public",
    "yes",
    "false",
]


def _dataset(headers, *rows):
    return tablib.Dataset(*rows, headers=headers)


def _row_problems(result):
    return [
        (row.import_type, [str(e.error) for e in row.errors], row.validation_error)
        for row in result.rows
        if row.errors or row.validation_error
    ]


class GuardianImportResourceTest(TestCase):
    def _import(self, *, dry_run=False):
        return GuardianImportResource().import_data(
            _dataset(GUARDIAN_HEADERS, GUARDIAN_ROW),
            dry_run=dry_run,
        )

    def test_import_creates_guardian_user(self):
        result = self._import()

        assert _row_problems(result) == []
        assert not result.has_errors()
        assert not result.has_validation_errors()

        user = User.objects.get(email="pat@example.com")
        assert user.role == "guardian"
        assert user.username == "pat@example.com"
        assert user.first_name == "Pat"
        assert user.last_name == "Parent"

        guardian = Guardian.objects.get(user=user)
        assert guardian.zip == "60605"
        assert guardian.phone == "312-555-0100"
        assert guardian.is_active is False

    def test_reimport_does_not_duplicate(self):
        self._import()
        result = self._import()

        assert _row_problems(result) == []
        assert User.objects.filter(email="pat@example.com").count() == 1
        assert Guardian.objects.count() == 1

    def test_dry_run_persists_nothing(self):
        result = self._import(dry_run=True)

        assert _row_problems(result) == []
        assert not User.objects.filter(email="pat@example.com").exists()
        assert Guardian.objects.count() == 0


class StudentResourceTest(TestCase):
    def setUp(self):
        guardian_user = User.objects.create(
            username="pat@example.com",
            email="pat@example.com",
            role="guardian",
        )
        self.guardian = Guardian.objects.create(user=guardian_user)

    def _import(self, *rows, dry_run=False):
        return StudentResource().import_data(
            _dataset(STUDENT_HEADERS, *(rows or [STUDENT_ROW])),
            dry_run=dry_run,
        )

    def test_import_creates_student(self):
        result = self._import()

        assert _row_problems(result) == []
        assert not result.has_errors()
        assert not result.has_validation_errors()

        student = Student.objects.get(first_name="Sam", last_name="Student")
        assert student.guardian == self.guardian
        assert student.birthday == date(2015, 1, 15)
        assert student.gender == "female"
        assert student.school_name == "Jones Elementary"
        assert student.school_type == "public"
        assert student.photo_release is True
        assert student.consent is False
        assert student.is_active is True

    def test_reimport_updates_without_duplicating(self):
        self._import()
        Student.objects.update(is_active=False)

        result = self._import()

        assert _row_problems(result) == []
        assert Student.objects.count() == 1
        assert Student.objects.get().is_active is True

    def test_unknown_guardian_email_is_row_error(self):
        row = list(STUDENT_ROW)
        row[2] = "nobody@example.com"

        result = self._import(row)

        assert result.has_errors()
        error = str(result.rows[0].errors[0].error)
        assert "guardian with email nobody@example.com not found" in error
        assert Student.objects.count() == 0

    def test_dry_run_persists_nothing(self):
        result = self._import(dry_run=True)

        assert _row_problems(result) == []
        assert Student.objects.count() == 0
