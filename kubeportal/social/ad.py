import ldap3
import social_core.exceptions
from django.conf import settings

import logging

logger = logging.getLogger('KubePortal')

domainname = settings.AUTH_AD_DOMAIN
server_adr = settings.AUTH_AD_SERVER if settings.AUTH_AD_SERVER else settings.AUTH_AD_DOMAIN


def is_available():
    try:
        server = ldap3.Server(server_adr, connect_timeout=1)
        conn = ldap3.Connection(server)
        conn.open()
        return True
    except Exception as e:
        logger.debug("Could not connect to AD server: {0}".format(str(e)))
        return False


def user_password(strategy, user, is_new=False, *args, details, backend, **kwargs):
    if backend.name != 'username':
        return

    if not settings.AUTH_AD_DOMAIN:
        raise social_core.exceptions.AuthUnreachableProvider(backend)


    # Connect to AD LDAP
    # Currently does not perform certificate check
    # Also, assume that all domain controllers support ldaps
    username = strategy.request_data()['username']
    password = strategy.request_data()['password']
    # User Principal Name
    upn = "{}@{}".format(username, domainname)
    server = ldap3.Server(server_adr, get_info=ldap3.DSA, connect_timeout=1)
    conn = ldap3.Connection(server, user=upn, password=password)
    try:
        conn.open()
        logger.info('LDAP connection to {} established.'.format(upn))

    except Exception:
        raise social_core.exceptions.AuthUnreachableProvider(backend)
    conn.start_tls()
    # validate password by binding
    if not conn.bind():
        logger.debug("AD LDAP bind with this password failed, refusing login.")
        raise social_core.exceptions.AuthFailed(backend,
                                                conn.result['description'])

    # lookup user attributes by searching for the UPN
    ctx = server.info.other['defaultNamingContext'][0]
    attributes = {'givenName': 'first_name', 'sn': 'last_name',
                  'displayName': 'fullname', 'mail': 'email'}
    res = conn.search(ctx, '(userPrincipalName={})'.format(upn),
                      attributes=list(attributes.keys()))
    if res:
        entry = conn.entries[0]
        for ldapname, socialname in attributes.items():
            try:
                details[socialname] = entry[ldapname].value
            except KeyError:
                pass
