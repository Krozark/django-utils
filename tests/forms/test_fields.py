from django import forms
from django.test import SimpleTestCase

from django_utils.forms import FileSizeField


class FileSizeFieldTests(SimpleTestCase):
    def setUp(self):
        self.field = FileSizeField(required=False)

    def test_clean_parses_units(self):
        for value, expected in (
            ("100MB", 100 * 1024**2),
            ("1 gb", 1024**3),
            ("500KB", 500 * 1024),
            ("1.5KB", 1536),
            ("42", 42),
            ("1,5KB", 1536),
        ):
            with self.subTest(value=value):
                self.assertEqual(self.field.clean(value), expected)

    def test_clean_empty_is_zero(self):
        self.assertEqual(self.field.clean(""), 0)

    def test_clean_rejects_invalid_value(self):
        with self.assertRaises(forms.ValidationError):
            self.field.clean("abc")

    def test_prepare_value_humanizes_bytes(self):
        for value, expected in (
            (0, 0),
            (None, 0),
            (512, "512B"),
            (2048, "2KB"),
            (1536, "1.5KB"),
            (3 * 1024**3, "3GB"),
        ):
            with self.subTest(value=value):
                self.assertEqual(self.field.prepare_value(value), expected)

    def test_prepare_value_keeps_non_numeric_values(self):
        self.assertEqual(self.field.prepare_value("abc"), "abc")
