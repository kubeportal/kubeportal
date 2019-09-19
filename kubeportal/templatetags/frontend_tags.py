from django import template
from django.conf import settings

from kubeportal.social.ad_ldap import ActiveDirectoryLdapAuth

register = template.Library()


@register.simple_tag
def ad_status():
    return ActiveDirectoryLdapAuth.ad_text_status()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.simple_tag
def settings_value_normalized(name):
    val = getattr(settings, name, "")
    return val.lower().replace(' ', '_')


@register.simple_tag(takes_context=True)
def placeholder_replace(context, text):
    with_ns = text.replace("{{namespace}}", context.request.user.service_account.namespace.name)
    with_both = with_ns.replace("{{serviceaccount}}", context.request.user.service_account.name)
    return with_both
