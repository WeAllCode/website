from django.test import SimpleTestCase

from coderdojochi.admin import strtobool

TRUE_VALUES = [
    "y",
    "Y",
    "yes",
    "YES",
    "Yes",
    "t",
    "T",
    "true",
    "TRUE",
    "True",
    "on",
    "ON",
    "On",
    "1",
]
FALSE_VALUES = [
    "n",
    "N",
    "no",
    "NO",
    "No",
    "f",
    "F",
    "false",
    "FALSE",
    "False",
    "off",
    "OFF",
    "Off",
    "0",
]
INVALID_VALUES = ["", "maybe", "2", "yess", " yes"]


class StrToBoolTests(SimpleTestCase):
    def test_true_values_return_true(self):
        for value in TRUE_VALUES:
            with self.subTest(value=value):
                assert strtobool(value) is True

    def test_false_values_return_false(self):
        for value in FALSE_VALUES:
            with self.subTest(value=value):
                assert strtobool(value) is False

    def test_invalid_values_raise_value_error(self):
        for value in INVALID_VALUES:
            with self.subTest(value=value), self.assertRaises(ValueError):  # noqa: PT027
                strtobool(value)
