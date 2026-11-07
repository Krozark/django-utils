from django.template import Context, Template
from django.test import SimpleTestCase


def render(source, **context):
    return Template("{% load django_utils_tags %}" + source).render(Context(context))


class LanguageFlagTests(SimpleTestCase):
    def test_known_languages(self):
        self.assertEqual(render("{{ code|language_flag }}", code="fr"), "🇫🇷")
        self.assertEqual(render("{{ code|language_flag }}", code="en"), "🇬🇧")

    def test_region_and_case_are_ignored(self):
        self.assertEqual(render("{{ code|language_flag }}", code="PT-br"), "🇵🇹")

    def test_unknown_language_gets_a_globe(self):
        for code in ("xx", "", None):
            with self.subTest(code=code):
                self.assertEqual(render("{{ code|language_flag }}", code=code), "🌐")
