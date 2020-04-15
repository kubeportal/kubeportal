from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger('KubePortal')

def permission_check(user, client):
    for group in user.portal_groups.all():
        for app in group.can_web_applications.all():
            if app.oidc_client == client:
                logger.debug("Access for user {0} through client {1} accepted".format(user, client))
                return None   # allowed
    logger.debug("Access for user {0} through client {1} denied".format(user, client))
    raise PermissionDenied    # not allowed


def oidc_login_hook(request, user, client):
    logger.debug("OIDC login for user {0}".format(user))
    return permission_check(user, client)
