from django import template
from django.template.loader import render_to_string

register = template.Library()


class GatedBlockNode(template.Node):
    template_name = "django_utils/gating/gated_block.html"

    def __init__(self, permission, nodelist):
        self.permission = permission
        self.nodelist = nodelist

    def render(self, context):
        context = {
            "permission": self.permission.resolve(context),
            "content": self.nodelist.render(context),
        }
        return render_to_string(self.template_name, context).strip()


@register.tag("gated_block")
def do_gated_block(parser, token):
    """Render the block only if the front-end ``permissions`` allow it, a locked message otherwise.

    The permission is the codename of a gated feature (see ``get_user_gated_features()``). The output is
    meant for Alpine.js, with a ``permissions`` object filled from ``{codename: bool}``; override the
    ``django_utils/gating/gated_block.html`` template to change the markup or the message.

    Usage::

        {% load django_utils_gating %}
        {% gated_block "set_on_start" %}
            ... gated content ...
        {% endgated_block %}
    """
    try:
        _tag_name, permission = token.split_contents()
    except ValueError as err:
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]} requires a single permission argument"
        ) from err
    nodelist = parser.parse(("endgated_block",))
    parser.delete_first_token()
    return GatedBlockNode(parser.compile_filter(permission), nodelist)
