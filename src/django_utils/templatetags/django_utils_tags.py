from django import template

register = template.Library()

_LANGUAGE_FLAGS = {
    "fr": "🇫🇷",
    "en": "🇬🇧",
    "de": "🇩🇪",
    "es": "🇪🇸",
    "it": "🇮🇹",
    "pt": "🇵🇹",
}
_DEFAULT_FLAG = "🌐"


@register.filter
def language_flag(lang_code):
    """Return the flag emoji of a language code (``"fr"``, ``"pt-br"``...), or a globe if it is unknown.

    Usage: ``{{ LANGUAGE_CODE|language_flag }}``
    """
    return _LANGUAGE_FLAGS.get(str(lang_code).split("-")[0].lower(), _DEFAULT_FLAG)
