from django import template
from django.conf import settings

from kubeportal.active_directory import is_available

register = template.Library()


@register.simple_tag
def ad_status():
    if settings.ACTIVE_DIRECTORY_DOMAIN:
        if is_available():
            return "available"
        else:
            return "unavailable"
    else:
        return "unconfigured"


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.simple_tag(takes_context=True)
def placeholder_replace(context, text):
    with_ns = text.replace("{{namespace}}", context.request.user.service_account.namespace.name)
    with_both = with_ns.replace("{{serviceaccount}}", context.request.user.service_account.name)
    return with_both
