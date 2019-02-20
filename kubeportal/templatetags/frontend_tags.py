from django import template
from django.conf import settings
from django.utils.html import format_html

from kubeportal.active_directory import is_available

register = template.Library()


@register.simple_tag
def ad_status():
    if settings.ACTIVE_DIRECTORY_DOMAIN:
        if is_available():
            result = format_html("Status: <i>{0}</i> <span class='text-success'>available</span> for login", settings.ACTIVE_DIRECTORY_DOMAIN)
        else:
            result = format_html("Status: <i>{0}</i> <span class='text-danger'>unavailable</span> for login", settings.ACTIVE_DIRECTORY_DOMAIN)
    else:
        result = format_html("Status: Active Directory login <span class='text-warning'>not configured</span>")
    return result


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")
