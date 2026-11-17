from django import forms
from django.utils.html import format_html, format_html_join

__all__ = ["StarRatingWidget"]


class StarRatingWidget(forms.Widget):
    """Interactive 5-star rating widget: clickable star buttons and a hidden input holding the value.

    The page provides the style (``.star-rating-widget``, ``.star``) and the script that fills the hidden
    ``.star-rating-input`` when a ``.star`` button is clicked.
    """

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs or {})
        widget_id = final_attrs.get("id", f"id_{name}")
        current_value = str(value) if value not in (None, "") else ""

        # ``value`` is echoed back from the submitted data when the form is invalid: everything is escaped.
        stars = format_html_join(
            "",
            '<button type="button" class="star" data-value="{0}" aria-label="{0}">★</button>',
            ((i,) for i in range(1, 6)),
        )
        return format_html(
            '<div class="star-rating-widget" role="radiogroup">{}'
            '<input type="hidden" name="{}" id="{}" class="star-rating-input" value="{}"></div>',
            stars,
            name,
            widget_id,
            current_value,
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
