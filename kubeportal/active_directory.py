import ldap3
import social_core.exceptions
from django.conf import settings

def user_password(strategy, user,is_new=False, *args, details, backend, **kwargs):
    if backend.name != 'username':
        return

    # Connect to AD LDAP
    # Currently does not perform certificate check
    # Also, assume that all domain controllers support ldaps
    domainname = settings.ACTIVE_DIRECTORY_DOMAIN
    username = strategy.request_data()['username']
    password = strategy.request_data()['password']
    # User Principal Name
    upn = "{}@{}".format(username, domainname)
    server = ldap3.Server(domainname, get_info=ldap3.DSA)
    conn = ldap3.Connection(server,
                                user=upn,
                                password=password)
    conn.open()
    conn.start_tls()
    # validate password by binding
    if not conn.bind():
        raise social_core.exceptions.AuthFailed(backend,
                                                conn.result['description'])

    # lookup user attributes by searching for the UPN
    ctx = server.info.other['defaultNamingContext'][0]
    attributes = {'givenName':'first_name', 'sn':'last_name',
                  'displayName':'fullname', 'mail':'email'}
    res = conn.search(ctx, '(userPrincipalName={})'.format(upn),
                      attributes=list(attributes.keys()))
    if res:
        entry = conn.entries[0]
        for ldapname, socialname in attributes.items():
            try:
                details[socialname] = entry[ldapname].value
            except KeyError:
                pass
