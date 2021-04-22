from dj_rest_auth.serializers import LoginSerializer as OriginalLoginSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer, extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse


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
class LoginSerializer(OriginalLoginSerializer):  # remove third optional field from library
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
    access_token_verify_url = serializers.SerializerMethodField()
    access_token_refresh_url = serializers.SerializerMethodField()
    refresh_token = serializers.CharField()
    user_url = serializers.SerializerMethodField()
    user_approval_url = serializers.SerializerMethodField()
    news_url = serializers.SerializerMethodField()
    infos_url = serializers.SerializerMethodField()
    storageclasses_url = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_user_url(self, obj):
        uid = obj['user'].pk
        request = self.context['request']
        return reverse(viewname='user', kwargs={'user_id': uid}, request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_user_approval_url(self, obj):
        uid = obj['user'].pk
        request = self.context['request']
        return reverse(viewname='user_approval', kwargs={'user_id': uid}, request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_news_url(self, obj):
        request = self.context['request']
        return reverse(viewname='news', request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_access_token_verify_url(self, obj):
        request = self.context['request']
        return reverse(viewname='token_verify', request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_access_token_refresh_url(self, obj):
        request = self.context['request']
        return reverse(viewname='token_refresh', request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_infos_url(self, obj):
        request = self.context['request']
        return reverse(viewname='info_overview', request=request)

    @extend_schema_field(OpenApiTypes.URI)
    def get_storageclasses_url(self, obj):
        request = self.context['request']
        return reverse(viewname='storageclasses', request=request)


