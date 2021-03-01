from drf_spectacular.utils import OpenApiExample, extend_schema_serializer, extend_schema
from rest_framework import serializers

from dj_rest_auth.serializers import LoginSerializer as OriginalLoginSerializer
from dj_rest_auth.serializers import JWTSerializer as OriginalJWTSerializer
from dj_rest_auth.views import LoginView as OriginalLoginView


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Local development example',
            value={
                'username': 'root',
                'password': 'rootpw',
            },
            request_only=True
        ),
        OpenApiExample(
            '',
            value={
                'user_id': 42,
                'group_ids': [5,7,13],
                'namespace': 'default',
                'jwt': '89ew4z7ro9ew47reswu'
            },
            response_only=True
        ),
    ]
)
class LoginSerializer(OriginalLoginSerializer): # remove third optional field from library
    username = serializers.CharField()
    password = serializers.CharField()

class JWTSerializer(OriginalJWTSerializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = serializers.HyperlinkedRelatedField(view_name='user', lookup_url_kwarg='user_id', read_only=True)

@extend_schema(
    summary="Perform API login with username and password.",
    description="Perform API login with username and password."  # Overwrite messy text from library
)
class LoginView(OriginalLoginView):
    serializer_class = LoginSerializer

    def get_response_serializer(self):
        # not using settings.py for the overloading, but this, avoids a circular import
        return JWTSerializer
