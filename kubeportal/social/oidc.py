from django.conf import settings
from social_core.backends.open_id_connect import OpenIdConnectAuth
from jose import jwk
from jose.utils import base64url_decode

class GenericOidc(OpenIdConnectAuth):
    """Generic OIDC relying party"""
    name = 'genericoidc'
    OIDC_ENDPOINT = settings.SOCIAL_AUTH_GENERICOIDC_ENDPOINT

    def find_valid_key(self, id_token):
        """Workaround for missing "alg" attribute in server answer"""
        for key in self.get_jwks_keys():
            if "alg" not in key:
                key['alg'] = 'RS256'
            rsakey = jwk.construct(key)
            message, encoded_sig = id_token.rsplit('.', 1)
            decoded_sig = base64url_decode(encoded_sig.encode('utf-8'))
            if rsakey.verify(message.encode('utf-8'), decoded_sig):
                return key


def userinfo(claims, user):
    claims['name'] = '{0} {1}'.format(user.first_name, user.last_name)
    claims['given_name'] = user.first_name
    claims['family_name'] = user.last_name
    claims['email'] = user.email
    return claims