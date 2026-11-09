from django.http import Http404
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from django_utils.api.handlers import custom_exception_handler


class CustomExceptionHandlerTests(SimpleTestCase):
    context = {"view": APIView(), "request": None}

    def test_wraps_validation_errors(self):
        response = custom_exception_handler(ValidationError({"name": ["Required"]}), self.context)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                "success": False,
                "status_code": 400,
                "data": None,
                "message": "name: Required",
                "errors": {"name": "Required"},
            },
        )

    def test_wraps_http_404(self):
        response = custom_exception_handler(Http404(), self.context)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["errors"], {"error": "Not found."})

    def test_ignores_unhandled_exceptions(self):
        self.assertIsNone(custom_exception_handler(RuntimeError(), self.context))
