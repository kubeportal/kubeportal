from drf_spectacular.utils import OpenApiExample, extend_schema_serializer, extend_schema
from rest_framework import serializers
from dj_rest_auth.serializers import LoginSerializer as OriginalLoginSerializer
from dj_rest_auth.serializers import JWTSerializer as OriginalJWTSerializer

from dj_rest_auth.views import LoginView as OriginalLoginView

class JWTSerializer(OriginalJWTSerializer):   # modify returned data structure from library
    user_id = serializers.IntegerField()
    group_ids = serializers.ListField(
        child = serializers.IntegerField()
    )
    namespace = serializers.CharField()
    jwt = serializers.CharField()

    def to_representation(self, instance):
        user = instance['user']
        groups = user.portal_groups.all()

        return {'user_id': user.pk,
                'group_ids': [group.pk for group in groups],
                'namespace': user.k8s_namespace().name,
                'jwt': str(instance['access_token'])
                }


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
                'id': 42,
                'firstname': 'Deniz',
                'jwt': '89ew4z7ro9ew47reswu'
            },
            response_only=True
        ),
    ]
)
class LoginSerializer(OriginalLoginSerializer): # remove third optional field from library
    username = serializers.CharField()
    password = serializers.CharField()


@extend_schema(
    summary="Perform API login with username and password.",
    description="Perform API login with username and password."  # Overwrite messy text from library
)
class LoginView(OriginalLoginView):
    serializer_class = LoginSerializer

    def get_response_serializer(self):
        return JWTSerializer
