from drf_spectacular.utils import OpenApiExample, extend_schema_serializer, extend_schema
from rest_framework import serializers
from rest_framework.reverse import reverse


from dj_rest_auth.serializers import LoginSerializer as OriginalLoginSerializer
from django.conf import settings
from django.utils.module_loading import import_string

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

class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    links = serializers.SerializerMethodField()

    def get_links(self, obj):
        uid = obj['user'].pk
        request = self.context['request']
        return {'user': reverse(viewname='user', kwargs={'user_id': uid}, request=request),
                'news': reverse(viewname='news', request=request)
                }

