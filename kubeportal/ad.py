import ldap3
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

logger = logging.getLogger('KubePortal')


class ActiveDirectoryBackend():
    domainname = settings.AUTH_AD_DOMAIN
    server_adr = settings.AUTH_AD_SERVER if settings.AUTH_AD_SERVER else settings.AUTH_AD_DOMAIN

    def authenticate(self, request, username=None, password=None):
        # Connect to AD LDAP
        # Currently does not perform certificate check
        # Also, assume that all domain controllers support ldaps

        if not self.server_adr:
            return None

        # User Principal Name
        upn = "{}@{}".format(username, self.domainname)
        server = ldap3.Server(self.server_adr, get_info=ldap3.DSA, connect_timeout=1)
        conn = ldap3.Connection(server, user=upn, password=password)
        try:
            conn.open()
        except Exception:
            logger.error('LDAP connection to Active Directory server failed. Denying access.')
            messages.error(request, 'Active Directory login not available.')
            return None

        conn.start_tls()

        # validate password by binding
        if not conn.bind():
            logger.error('LDAP bind to Active Directory server failed. Denying access.')
            messages.error(request, 'Active Directory login failed, invalid credentials.')
            return None

        # lookup user attributes by searching for the UPN
        ctx = server.info.other['defaultNamingContext'][0]
        # first name, last name, display name, email, alternative email
        attributes = ['givenName', 'sn', 'mail', 'proxyAddresses']
        res = conn.search(ctx, '(userPrincipalName={})'.format(upn),
                          attributes=attributes)

        if res:
            entries = conn.entries[0]
            defaults = {}
            defaults['first_name'] = entries['givenName'].value if entries['givenName'] else ""
            defaults['last_name'] = entries['sn'].value if entries['sn'] else ""
            defaults['email'] = entries['mail'].value.lower() if entries['mail'] else ""
            defaults['username'] = username
            if entries['proxyAddresses']:
                defaults['alt_mails'] = [i.lower().replace("unix:", "").replace("smtp:", "") for i in entries['proxyAddresses'].value]

            try:
                user, created = User.objects.update_or_create(username__iexact=username, defaults=defaults)
                if created:
                    logger.debug("Created new user for Active Directory account {}".format(username))
                else:
                    logger.debug("Found existing user for Active Directory account {}".format(username))

            except Exception as e:
                logger.error("Problem while finding / creating user: {}".format(e))
                messages.error(request, "Problem while checking the Active Directory user.")
                return None

            logger.debug(user)
            return user
        else:
            logger.error('Coud not fetch user information from Active Directory. Denying access.')
            messages.error(request, 'Missing user information in Active Directory, access denied.')
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
