from django.test import SimpleTestCase

from django_utils.api.envelope import (
    error_envelope,
    format_errors,
    get_error_message,
    get_success_message,
    is_envelope,
    success_envelope,
)


class IsEnvelopeTests(SimpleTestCase):
    def test_detects_envelope(self):
        self.assertTrue(is_envelope(success_envelope({"a": 1}, 200)))
        self.assertTrue(is_envelope(error_envelope({"a": ["bad"]}, 400)))

    def test_rejects_other_data(self):
        for data in (None, [], {"success": True}, {"a": 1}):
            with self.subTest(data=data):
                self.assertFalse(is_envelope(data))


class MessageTests(SimpleTestCase):
    def test_success_messages(self):
        paginated = {"results": [], "pagination": {}}
        self.assertEqual(get_success_message(paginated, 200), "Data retrieved successfully")
        self.assertEqual(get_success_message({}, 201), "Resource created successfully")
        self.assertEqual(get_success_message(None, 204), "Resource deleted successfully")
        self.assertEqual(get_success_message({}, 200), "Request successful")

    def test_error_messages(self):
        for data, expected in (
            ({"detail": "Not found."}, "Not found."),
            ({"non_field_errors": ["Bad", "Worse"]}, "Bad"),
            ({"non_field_errors": []}, "Validation error"),
            ({"error": "Boom"}, "Boom"),
            ({"name": ["Required", "Other"]}, "name: Required"),
            ({"name": "Required"}, "name: Required"),
            ({}, "An error occurred"),
            (["First", "Second"], "First"),
            ([], "An error occurred"),
            ("text", "An error occurred"),
        ):
            with self.subTest(data=data):
                self.assertEqual(get_error_message(data), expected)


class FormatErrorsTests(SimpleTestCase):
    def test_joins_messages_of_a_field(self):
        self.assertEqual(format_errors({"password": ["Too short", "Too common"]}), {"password": "Too short Too common"})

    def test_non_field_errors_use_the_error_key(self):
        self.assertEqual(format_errors({"detail": "Nope"}), {"error": "Nope"})
        self.assertEqual(format_errors({"non_field_errors": ["A", "B"]}), {"error": "A B"})

    def test_lists_and_strings(self):
        self.assertEqual(format_errors(["A", "B"]), {"error": "A B"})
        self.assertEqual(format_errors("A"), {"error": "A"})

    def test_none_and_empty_values(self):
        self.assertIsNone(format_errors(None))
        self.assertEqual(format_errors({"name": []}), {"name": "Invalid value"})

    def test_is_idempotent(self):
        errors = format_errors({"name": ["A", "B"], "detail": "C"})
        self.assertEqual(format_errors(errors), errors)


class EnvelopeBuildersTests(SimpleTestCase):
    def test_success(self):
        self.assertEqual(
            success_envelope({"a": 1}, 200),
            {"success": True, "status_code": 200, "data": {"a": 1}, "message": "Request successful", "errors": None},
        )

    def test_error(self):
        self.assertEqual(
            error_envelope({"name": ["Required"]}, 400),
            {
                "success": False,
                "status_code": 400,
                "data": None,
                "message": "name: Required",
                "errors": {"name": "Required"},
            },
        )
