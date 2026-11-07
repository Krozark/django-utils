from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase, override_settings

from tests.settings import TEMPLATES


def render(source, **context):
    return Template("{% load django_utils_gating %}" + source).render(Context(context))


class GatedBlockTests(SimpleTestCase):
    def test_renders_both_alpine_branches(self):
        html = render("{% gated_block 'use_secret' %}<b>content</b>{% endgated_block %}")

        self.assertIn('<template x-if="permissions.use_secret"><div><b>content</b></div></template>', html)
        self.assertIn('<template x-if="!permissions.use_secret">', html)
        self.assertIn("This feature is not available with your current plan.", html)

    def test_permission_can_be_a_variable_and_is_escaped(self):
        html = render("{% gated_block perm %}x{% endgated_block %}", perm='a"b')

        self.assertIn("permissions.a&quot;b", html)

    def test_content_is_rendered_with_the_context(self):
        self.assertIn(
            "<i>hello</i>", render("{% gated_block 'p' %}<i>{{ word }}</i>{% endgated_block %}", word="hello")
        )

    def test_requires_one_permission_argument(self):
        for source in ("{% gated_block %}{% endgated_block %}", "{% gated_block 'a' 'b' %}{% endgated_block %}"):
            with self.subTest(source=source), self.assertRaises(TemplateSyntaxError):
                render(source)

    def test_markup_can_be_overridden(self):
        templates = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "OPTIONS": {
                    "loaders": [
                        (
                            "django.template.loaders.locmem.Loader",
                            {"django_utils/gating/gated_block.html": "[{{ permission }}|{{ content }}]"},
                        ),
                        *TEMPLATES[0]["OPTIONS"].get("loaders", ["django.template.loaders.app_directories.Loader"]),
                    ],
                },
            }
        ]
        with override_settings(TEMPLATES=templates):
            self.assertEqual(render("{% gated_block 'p' %}x{% endgated_block %}"), "[p|x]")
