from django import forms
from django.utils.safestring import mark_safe

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

        stars = "".join(
            f'<button type="button" class="star" data-value="{i}" aria-label="{i}">★</button>' for i in range(1, 6)
        )
        hidden = (
            f'<input type="hidden" name="{name}" id="{widget_id}" class="star-rating-input" value="{current_value}">'
        )
        return mark_safe(f'<div class="star-rating-widget" role="radiogroup">{stars}{hidden}</div>')

    def value_from_datadict(self, data, files, name):
        return data.get(name)
