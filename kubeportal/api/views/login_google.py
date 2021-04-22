from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from .login import JWTSerializer
from drf_spectacular.utils import extend_schema

class GoogleLoginSerializer(SocialLoginSerializer):
    code = None
    id_token = None

@extend_schema(
    request=GoogleLoginSerializer,
    responses=JWTSerializer
)
class GoogleLoginView(SocialLoginView):
    """
    Perform Google OAuth login by providing a Google access token.
    The token must be obtained by the frontend application through an
    implicit grant flow.
    """
    adapter_class = GoogleOAuth2Adapter
    serializer_class = GoogleLoginSerializer

