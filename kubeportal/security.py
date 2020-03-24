from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger('KubePortal')

def permission_check(user, client):
	#raise PermissionDenied
	return None # means everything is ok

def oidc_login_hook(request, user, client):
    logger.debug("OIDC login request for {0}".format(user))
    return permission_check(user, client)
