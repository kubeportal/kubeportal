import logging

logger = logging.getLogger('KubePortal')


def oidc_idtoken_hook(id_token, user, token, request, **kwargs):
    logger.debug("OIDC ID token request for {0}".format(user))
    import pdb; pdb.set_trace()
    return id_token

def oidc_login_hook(request, user, client):
    logger.debug("OIDC login request for {0}".format(user))
    import pdb; pdb.set_trace()
    return None
