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
    webapp_ids = serializers.ListField(
        child = serializers.IntegerField()
    )
    k8s_namespace = serializers.CharField()
    access_token = serializers.CharField()

    def to_representation(self, instance):
        user = instance['user']
        k8s_namespace = user.k8s_namespace()        

        return {'user_id': user.user_id(),
                'group_ids': user.group_ids(),
                'webapp_ids': user.webapp_ids(),
                'k8s_namespace': k8s_namespace.name if k8s_namespace else "",
                'access_token': str(instance['access_token'])
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


@extend_schema(
    summary="Perform API login with username and password.",
    description="Perform API login with username and password."  # Overwrite messy text from library
)
class LoginView(OriginalLoginView):
    serializer_class = LoginSerializer

    def get_response_serializer(self):
        return JWTSerializer
