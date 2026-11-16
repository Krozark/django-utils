"""Fluid forms: render a whole form (``{% render_fluid_form %}``) or one field (``{% fluid_form_field %}``).

The templates are under ``django_utils/forms/`` and can be overridden; the style (``.form-row``, ``.form-input``,
``.form-grid``...) is provided by the project.
"""

from django import template
from django.forms import (
    CheckboxInput,
    DateInput,
    DateTimeInput,
    EmailInput,
    FileInput,
    NumberInput,
    PasswordInput,
    RadioSelect,
    Select,
    SelectMultiple,
    Textarea,
    TextInput,
    TimeInput,
    URLInput,
)
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from django_utils.forms.widgets import StarRatingWidget

register = template.Library()

# Template paths for each field type
FIELD_TEMPLATES = {
    "checkbox": "django_utils/forms/field_checkbox.html",
    "switch": "django_utils/forms/field_switch.html",
    "file": "django_utils/forms/field_file.html",
    "star_rating": "django_utils/forms/field_star_rating.html",
    "input": "django_utils/forms/field_input.html",
}


@register.simple_tag
def fluid_form(form):
    """
    Template tag that automatically applies fluid styles to all form fields.
    Usage: {% fluid_form form %}
    """

    # Mapping of widgets to CSS classes
    widget_class_mapping = {
        TextInput: "form-input",
        EmailInput: "form-input",
        PasswordInput: "form-input",
        NumberInput: "form-input",
        URLInput: "form-input",
        DateInput: "form-input",
        TimeInput: "form-input",
        DateTimeInput: "form-input",
        Textarea: "form-input form-textarea",
        Select: "form-input form-select",
        SelectMultiple: "form-input form-select",
        CheckboxInput: "form-checkbox",
        RadioSelect: "form-radio",
        FileInput: "form-file",
    }

    # Iterate through all form fields
    for _, field in form.fields.items():
        widget = field.widget
        widget_type = type(widget)

        # Apply the appropriate CSS class
        if widget_type in widget_class_mapping:
            css_class = widget_class_mapping[widget_type]

            # Get existing classes
            existing_classes = widget.attrs.get("class", "")

            # Add the new class if it doesn't already exist
            if css_class not in existing_classes:
                new_classes = f"{existing_classes} {css_class}".strip()
                widget.attrs["class"] = new_classes

        # Add default placeholders if not already defined
        if isinstance(widget, TextInput | EmailInput | PasswordInput) and not widget.attrs.get("placeholder"):
            if hasattr(field, "label") and field.label:
                widget.attrs["placeholder"] = field.label

        # Add the required attribute visually if the field is required
        if field.required and "required" not in widget.attrs:
            widget.attrs["required"] = True

    return ""


@register.inclusion_tag("django_utils/forms/form.html", takes_context=True)
def render_fluid_form(context, form, show_labels=True, grid_columns=1):
    """
    Inclusion template tag to fully render a form with fluid styling.
    Usage: {% render_fluid_form form show_labels=True grid_columns=2 %}
    """
    # Apply fluid styles
    fluid_form(form)

    return {
        "form": form,
        "show_labels": show_labels,
        "grid_columns": grid_columns,
        "messages": context.get("messages", []),
    }


def _detect_field_type(widget):
    """Auto-detect the field type from the widget class."""
    if isinstance(widget, StarRatingWidget):
        return "star_rating"
    elif isinstance(widget, CheckboxInput):
        return "checkbox"
    elif isinstance(widget, RadioSelect):
        return "radio"
    elif isinstance(widget, FileInput):
        return "file"
    return "input"


def _apply_input_css_classes(field, widget):
    """Apply CSS classes for default input fields."""
    existing_class = widget.attrs.get("class", "")
    if "form-input" not in existing_class:
        widget.attrs["class"] = f"{existing_class} form-input".strip()

    if isinstance(widget, Textarea) and "form-textarea" not in existing_class:
        widget.attrs["class"] += " form-textarea"

    if isinstance(widget, Select | SelectMultiple) and "form-select" not in existing_class:
        widget.attrs["class"] += " form-select"


@register.simple_tag
def fluid_form_field(field, field_type="auto", label="", description="", wrapper_class="form-row"):
    """
    Tag to render an individual field with automatic type detection.
    Uses separate template files for each field type.
    Usage: {% fluid_form_field form.email %}
    """
    widget = field.field.widget

    if field_type == "auto":
        field_type = _detect_field_type(widget)

    # Layout modifiers: a form lists in `fluid_full_width` the fields that take the whole row of a multi-column grid,
    # and a captcha (image + field) is shown on one line.
    if field.name in getattr(field.form, "fluid_full_width", ()):
        wrapper_class += " form-row--full"
    if type(field.field).__name__ == "CaptchaField":  # by name: no hard dependency on django-simple-captcha
        wrapper_class += " form-row--captcha"

    context = {
        "field": field,
        "label": label or field.label,
        "description": description,
        "wrapper_class": wrapper_class,
    }

    if field_type == "file":
        field.field.widget.attrs["class"] = "form-file"
        context["field_id"] = field.auto_id or f"id_{field.name}"
    elif field_type == "input":
        _apply_input_css_classes(field, widget)
    # star_rating: widget renders its own HTML, no CSS class needed

    # Use "input" template for radio (same layout)
    template_name = FIELD_TEMPLATES.get(field_type, FIELD_TEMPLATES["input"])
    tpl = template.loader.get_template(template_name)
    return mark_safe(tpl.render(context))


@register.simple_tag
def star_rating_field(name, value=None, label="", required=False, wrapper_class="form-row"):
    """
    Render a standalone star rating field without a Django form object.
    Useful in HTMX partials that work with raw serialized data.
    Usage: {% star_rating_field "rating" review.rating label=_("Rating") %}
    """
    widget = StarRatingWidget()
    field_html = widget.render(name, value)

    parts = [f'<div class="{conditional_escape(wrapper_class)}">']
    if label:
        req = " required" if required else ""
        parts.append(f'<label class="form-label{req}">{conditional_escape(label)}</label>')
    parts.append(field_html)
    parts.append("</div>")
    return mark_safe("".join(parts))
