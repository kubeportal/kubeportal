from django import template
from django.conf import settings

from kubeportal.kubernetes import get_apiserver

register = template.Library()


@register.simple_tag
def apiserver():
    return get_apiserver()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.simple_tag
def settings_value_normalized(name):
    val = getattr(settings, name, "")
    return val.lower().replace(' ', '_')


@register.simple_tag(takes_context=True)
def placeholder_replace(context, text):
    if text is None:
        return ""

    try:
        ns = context.request.user.service_account.namespace.name
        svc = context.request.user.service_account.name
    except:
        ns = ""
        svc = ""
    with_ns = text.replace("{{namespace}}", ns)
    with_both = with_ns.replace("{{serviceaccount}}", svc)
    return with_both
