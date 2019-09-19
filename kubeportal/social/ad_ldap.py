'''
A Python social backend that performs an active directory login.
'''

import ldap3
from social_core.backends.base import BaseAuth
from social_core.exceptions import AuthFailed, AuthUnreachableProvider
from django.urls import get_script_prefix
from django.conf import settings

import logging
logger = logging.getLogger('KubePortal')


class ActiveDirectoryLdapAuth(BaseAuth):
    name = 'ad_ldap'
    ad_attributes = {'first_name': 'givenName',
                     'last_name': 'sn',
                     'fullname': 'displayName',
                     'email': 'mail'}

    def get_user_id(self, details, response):
        return response['username']

    def get_user_details(self, response):
        return response

    def auth_url(self):
        """Must return redirect URL to auth provider."""
        return get_script_prefix() + 'complete/%s/' % self.name

    @classmethod
    def get_settings(cls):
        if not settings.AUTH_AD_DOMAIN:
            return None, None
        domainname = settings.AUTH_AD_DOMAIN
        server_adr = settings.AUTH_AD_SERVER if settings.AUTH_AD_SERVER else settings.AUTH_AD_DOMAIN
        return domainname, server_adr

    @classmethod
    def ad_text_status(cls):
        domainname, server_adr = cls.get_settings()
        if not server_adr:
            return "unconfigured"
        try:
            server = ldap3.Server(server_adr, connect_timeout=1)
            conn = ldap3.Connection(server)
            conn.open()
            return "available"
        except Exception:
            return "unavailable"

    def try_ad_login(self, username, password):
        domainname, server_adr = ActiveDirectoryLdapAuth.get_settings()
        if not domainname:
            raise AuthUnreachableProvider(self, "Missing setting AUTH_AD_DOMAIN.")

        # Connect to AD LDAP
        # Currently does not perform certificate check
        # Also, assume that all domain controllers support ldaps

        # User Principal Name
        upn = "{}@{}".format(username, domainname)
        server = ldap3.Server(server_adr, get_info=ldap3.DSA, connect_timeout=1)
        conn = ldap3.Connection(server, user=upn, password=password)
        try:
            conn.open()
        except Exception:
            logger.error("Could not connect to " + server_adr)
            raise AuthUnreachableProvider(self, 'Could not connect to {0}.'.format(server_adr))
        conn.start_tls()
        # validate password by binding
        if not conn.bind():
            logger.error("Could not bind to {0} as user {1}.".format(server_adr, username))
            raise AuthFailed(self, 'Invalid credentials.')

        # Login successful
        logger.debug("Login successfull for AD user " + username)
        result = {'username': username}

        # lookup user attributes by searching for the UPN
        ctx = server.info.other['defaultNamingContext'][0]
        res = conn.search(ctx, '(userPrincipalName={})'.format(upn),
                          attributes=list(self.ad_attributes.values()))
        if res:
            logger.debug("Got user information from AD: " + str(conn.entries[0]))
            for social_attr, ldap_attr in self.ad_attributes.items():
                if ldap_attr in conn.entries[0]:
                    result[social_attr] = conn.entries[0][ldap_attr].value
        return result

    def auth_complete(self, *args, **kwargs):
        username = self.strategy.request_data()['username']
        password = self.strategy.request_data()['password']
        response = self.try_ad_login(username, password)
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
