from django.template.loader import render_to_string
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from .envelope import error_envelope, is_envelope, success_envelope

__all__ = [
    "StandardJSONRenderer",
    "HTMXRenderer",
]


class StandardJSONRenderer(JSONRenderer):
    """JSON renderer wrapping responses in the standard envelope, unless they already are."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if response is not None and not is_envelope(data):
            if 200 <= response.status_code < 300:
                data = success_envelope(data, response.status_code)
            else:
                data = error_envelope(data, response.status_code)

        return super().render(data, accepted_media_type, renderer_context)


class HTMXRenderer(TemplateHTMLRenderer):
    """Renderer for HTMX requests that returns HTML partials.

    Activated by adding ``?format=htmx`` to API URLs (``format="htmx"`` avoids the conflict with the
    browsable API renderer, whose format is ``html``).

    The template is selected from the model of the view and its action::

        <partials_path>/<model>_<suffix>_partial.html

    falling back to a generic ``django_utils/htmx/default_partial.html``. Subclass it to change where
    the partials live (``partials_path``) or how actions map to suffixes (``action_suffixes``).
    The template context contains ``data``, ``view``, ``request``, ``response`` and, for the
    ``retrieve`` action, ``object``.
    """

    media_type = "text/htmx"
    format = "htmx"

    #: Directory of the partials; ``{app_label}`` is replaced by the app label of the view's model.
    partials_path = "{app_label}/partials"
    #: Template suffix per view action; unknown actions use the action name itself.
    action_suffixes = {
        "list": "list",
        "retrieve": "detail",
        "create": "form",
        "update": "form",
        "partial_update": "form",
    }
    default_template_name = "django_utils/htmx/default_partial.html"

    def get_template_names(self, response, view):
        model = view.get_queryset().model
        directory = self.partials_path.format(app_label=model._meta.app_label)
        action = self.get_action(view)
        suffix = self.action_suffixes.get(action, action)
        return [f"{directory}/{model.__name__.lower()}_{suffix}_partial.html", self.default_template_name]

    @staticmethod
    def get_action(view):
        """The action of a viewset, or the lower-cased HTTP method for the other views."""
        return getattr(view, "action", None) or view.request.method.lower()

    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context["view"]
        request = renderer_context["request"]
        response = renderer_context["response"]

        context = {
            # Unwrap data if it is in the standard envelope (e.g. error responses).
            "data": data["data"] if is_envelope(data) else data,
            "view": view,
            "request": request,
            "response": response,
        }
        if self.get_action(view) == "retrieve" and response.status_code < 400:
            context["object"] = view.get_object()

        return render_to_string(self.get_template_names(response, view), context, request=request)
