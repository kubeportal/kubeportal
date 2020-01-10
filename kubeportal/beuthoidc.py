from social_core.backends.open_id_connect import OpenIdConnectAuth

class BeuthTestOIDC(OpenIdConnectAuth):
    """Beuth idp-test OIDC provider"""
    name = 'beuthtest'
    OIDC_ENDPOINT = 'https://idp-test.beuth-hochschule.de'
    AUTHORIZATION_URL = 'https://idp-test.beuth-hochschule.de/idp/profile/oidc/authorize'
    ACCESS_TOKEN_URL = 'https://idp-test.beuth-hochschule.de/idp/profile/oidc/token'
    # REFRESH_TOKEN_URL = 'https://idp-test.beuth-hochschule.de/idp/profile/oidc/token'
    # DEFAULT_SCOPE = "oidc"
    # SCOPE_SEPARATOR = ','