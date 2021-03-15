from drf_spectacular.utils import OpenApiExample, extend_schema_serializer, extend_schema, extend_schema_field
from drf_spectacular.types import OpenApiTypes
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
    ]
)
class LoginSerializer(OriginalLoginSerializer): # remove third optional field from library
    """
    The API serializer for username / password login.
    """
    username = serializers.CharField()
    password = serializers.CharField()
    email = None

class JWTSerializer(serializers.Serializer):
    """
    The API serializer for getting security information after successful login.
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user_url = serializers.SerializerMethodField()
    news_url = serializers.SerializerMethodField()
    infos_url = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_user_url(self, obj):
        uid = obj['user'].pk
        request = self.context['request']
        return reverse(viewname='user', kwargs={'user_id': uid}, request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_news_url(self, obj):
        request = self.context['request']
        return reverse(viewname='news', request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_infos_url(self, obj):
        request = self.context['request']
        return reverse(viewname='info_overview', request=request)

