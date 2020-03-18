import logging

logger = logging.getLogger('KubePortal')


def oidc_hook(id_token, user, token, request, **kwargs):
    logger.debug("OIDC user info requested for {0}".format(user))
    return id_token
