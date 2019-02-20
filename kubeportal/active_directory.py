import ldap3
import social_core.exceptions
from django.conf import settings


def is_available():
    domainname = settings.ACTIVE_DIRECTORY_DOMAIN
    try:
        server = ldap3.Server(domainname, connect_timeout=1)
        conn = ldap3.Connection(server)
        conn.open()
        conn.close()
        return True
    except Exception:
        return False


def user_password(strategy, user, is_new=False, *args, details, backend, **kwargs):
    if backend.name != 'username':
        return

    if not settings.ACTIVE_DIRECTORY_DOMAIN:
        raise social_core.exceptions.AuthUnreachableProvider(backend)

    # Connect to AD LDAP
    # Currently does not perform certificate check
    # Also, assume that all domain controllers support ldaps
    domainname = settings.ACTIVE_DIRECTORY_DOMAIN
    username = strategy.request_data()['username']
    password = strategy.request_data()['password']
    # User Principal Name
    upn = "{}@{}".format(username, domainname)
    server = ldap3.Server(domainname, get_info=ldap3.DSA, connect_timeout=1)
    conn = ldap3.Connection(server, user=upn, password=password)
    try:
        conn.open()
    except Exception:
        raise social_core.exceptions.AuthUnreachableProvider(backend)
    conn.start_tls()
    # validate password by binding
    if not conn.bind():
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
