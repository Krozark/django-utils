from django import forms
from django.template import Context, Template
from django.test import SimpleTestCase

from django_utils.forms.widgets import StarRatingWidget
from django_utils.templatetags.django_utils_forms import (
    fluid_form,
    fluid_form_field,
    render_fluid_form,
    star_rating_field,
)

from .sample_form import SampleForm

__all__ = [
    "FluidFormTemplateTagTests",
    "FluidFormIntegrationTests",
    "FluidFormFieldTemplateTagTests",
    "FluidFormFieldIntegrationTests",
    "RenderFluidFormTemplateTagTests",
    "FluidFormLayoutTests",
    "StarRatingWidgetTests",
]


class FluidFormTemplateTagTests(SimpleTestCase):
    """Tests for fluid_form template tag."""

    def test_fluid_form_adds_css_classes(self):
        """Test that fluid_form adds appropriate CSS classes."""
        form = SampleForm()
        fluid_form(form)

        self.assertIn("form-input", form.fields["name"].widget.attrs.get("class", ""))
        self.assertIn("form-input", form.fields["email"].widget.attrs.get("class", ""))
        self.assertIn("form-input", form.fields["password"].widget.attrs.get("class", ""))
        self.assertIn("form-textarea", form.fields["message"].widget.attrs.get("class", ""))
        self.assertIn("form-checkbox", form.fields["agree"].widget.attrs.get("class", ""))
        self.assertIn("form-file", form.fields["document"].widget.attrs.get("class", ""))

    def test_fluid_form_adds_placeholder(self):
        """Test that fluid_form adds placeholders from labels."""
        form = SampleForm()
        fluid_form(form)

        self.assertEqual(form.fields["name"].widget.attrs.get("placeholder"), "Your Name")
        self.assertEqual(form.fields["email"].widget.attrs.get("placeholder"), "Email Address")
        self.assertEqual(form.fields["password"].widget.attrs.get("placeholder"), "Password")

    def test_fluid_form_adds_required_attribute(self):
        """Test that fluid_form adds required attribute for required fields."""
        form = SampleForm()
        fluid_form(form)

        self.assertTrue(form.fields["name"].widget.attrs.get("required"))
        self.assertTrue(form.fields["email"].widget.attrs.get("required"))
        self.assertIsNone(form.fields["message"].widget.attrs.get("required"))

    def test_fluid_form_preserves_existing_classes(self):
        """Test that fluid_form preserves existing CSS classes."""
        form = SampleForm()
        form.fields["name"].widget.attrs["class"] = "custom-class"
        fluid_form(form)

        classes = form.fields["name"].widget.attrs.get("class", "")
        self.assertIn("custom-class", classes)
        self.assertIn("form-input", classes)

    def test_fluid_form_returns_empty_string(self):
        """Test that fluid_form returns empty string."""
        form = SampleForm()
        result = fluid_form(form)
        self.assertEqual(result, "")


class FluidFormIntegrationTests(SimpleTestCase):
    """Integration tests for fluid_form in templates."""

    def test_fluid_form_tag_in_template(self):
        """Test using fluid_form tag in a template."""
        template = Template("""
            {% load django_utils_forms %}
            {% fluid_form form %}
            {{ form.name }}
        """)
        form = SampleForm()
        context = Context({"form": form})
        rendered = template.render(context)

        self.assertIn("form-input", rendered)


class FluidFormFieldTemplateTagTests(SimpleTestCase):
    """Tests for fluid_form_field template tag."""

    def test_fluid_form_field_renders_input(self):
        """Test that fluid_form_field renders input field."""
        form = SampleForm()
        result = fluid_form_field(form["name"])

        self.assertIn("form-row", result)
        self.assertIn("form-label", result)
        self.assertIn("Your Name", result)

    def test_fluid_form_field_renders_checkbox(self):
        """Test that fluid_form_field renders checkbox field."""
        form = SampleForm()
        result = fluid_form_field(form["agree"])

        self.assertIn("checkbox", result.lower())
        self.assertIn("I agree", result)

    def test_fluid_form_field_renders_file(self):
        """Test that fluid_form_field renders file field."""
        form = SampleForm()
        result = fluid_form_field(form["document"])

        self.assertIn("form-file", result)
        self.assertIn("Upload", result)

    def test_fluid_form_field_with_custom_label(self):
        """Test that fluid_form_field can use custom label."""
        form = SampleForm()
        result = fluid_form_field(form["name"], label="Custom Label")

        self.assertIn("Custom Label", result)

    def test_fluid_form_field_with_description(self):
        """Test that fluid_form_field renders description."""
        form = SampleForm()
        result = fluid_form_field(form["name"], description="Help text here")

        self.assertIn("Help text here", result)
        self.assertIn("form-help-text", result)

    def test_fluid_form_field_shows_errors(self):
        """Test that fluid_form_field shows field errors."""
        form = SampleForm(data={})
        form.is_valid()  # Triggers validation
        result = fluid_form_field(form["name"])

        self.assertIn("error", result.lower())

    def test_fluid_form_field_switch_type(self):
        """Test that fluid_form_field renders switch type."""
        form = SampleForm()
        result = fluid_form_field(form["agree"], field_type="switch")

        self.assertIn("switch", result.lower())


class FluidFormFieldIntegrationTests(SimpleTestCase):
    """Integration tests for fluid_form_field in templates."""

    def test_fluid_form_field_tag_in_template(self):
        """Test using fluid_form_field tag in a template."""
        template = Template("""
            {% load django_utils_forms %}
            {% fluid_form_field form.email %}
        """)
        form = SampleForm()
        context = Context({"form": form})
        rendered = template.render(context)

        self.assertIn("Email Address", rendered)
        self.assertIn("form-row", rendered)


class RenderFluidFormTemplateTagTests(SimpleTestCase):
    """Tests for render_fluid_form template tag."""

    def test_render_fluid_form_returns_context(self):
        """Test that render_fluid_form returns correct context."""
        form = SampleForm()
        context = {"messages": []}
        result = render_fluid_form(context, form, show_labels=True, grid_columns=2)

        self.assertEqual(result["form"], form)
        self.assertEqual(result["show_labels"], True)
        self.assertEqual(result["grid_columns"], 2)

    def test_render_fluid_form_applies_styles(self):
        """Test that render_fluid_form applies fluid styles."""
        form = SampleForm()
        context = {"messages": []}
        render_fluid_form(context, form)

        # Check that styles were applied
        self.assertIn("form-input", form.fields["name"].widget.attrs.get("class", ""))

    def test_render_fluid_form_default_values(self):
        """Test that render_fluid_form works with default values."""
        form = SampleForm()
        context = {"messages": []}
        result = render_fluid_form(context, form)

        self.assertIn("form", result)
        self.assertIn("show_labels", result)
        self.assertIn("grid_columns", result)

    def test_render_fluid_form_passes_messages(self):
        """Test that render_fluid_form passes messages to context."""
        form = SampleForm()
        messages = ["Test message"]
        context = {"messages": messages}
        result = render_fluid_form(context, form)

        self.assertEqual(result["messages"], messages)


class FluidFormLayoutTests(SimpleTestCase):
    """The layout modifiers of the wrapper of a field."""

    class ContactForm(forms.Form):
        fluid_full_width = ("message",)

        name = forms.CharField()
        message = forms.CharField(widget=forms.Textarea)

    def test_a_listed_field_takes_the_whole_row(self):
        form = self.ContactForm()

        self.assertIn("form-row--full", fluid_form_field(form["message"]))
        self.assertNotIn("form-row--full", fluid_form_field(form["name"]))

    def test_a_form_without_the_attribute_has_no_full_row(self):
        self.assertNotIn("form-row--full", fluid_form_field(SampleForm()["name"]))

    def test_a_captcha_is_shown_on_one_line(self):
        class CaptchaField(
            forms.CharField
        ):  # detected by its name: the library does not depend on django-simple-captcha
            pass

        class CaptchaForm(forms.Form):
            captcha = CaptchaField()

        self.assertIn("form-row--captcha", fluid_form_field(CaptchaForm()["captcha"]))

    def test_the_columns_are_a_css_variable(self):
        html = Template("{% load django_utils_forms %}{% render_fluid_form form grid_columns=2 %}").render(
            Context({"form": SampleForm()})
        )

        self.assertIn("--form-columns: 2", html)


class StarRatingWidgetTests(SimpleTestCase):
    class RatingForm(forms.Form):
        rating = forms.IntegerField(widget=StarRatingWidget())

    def test_renders_five_stars_and_the_value(self):
        html = StarRatingWidget().render("rating", 3, {"id": "id_rating"})

        self.assertEqual(html.count('class="star"'), 5)
        self.assertIn('name="rating"', html)
        self.assertIn('value="3"', html)

    def test_the_value_comes_from_the_data(self):
        self.assertEqual(StarRatingWidget().value_from_datadict({"rating": "4"}, {}, "rating"), "4")

    def test_a_field_with_the_widget_uses_the_star_template(self):
        self.assertIn("star-rating-widget", fluid_form_field(self.RatingForm()["rating"]))

    def test_standalone_field(self):
        html = star_rating_field("rating", 2, label="Rating")

        self.assertIn("Rating", html)
        self.assertIn('value="2"', html)
