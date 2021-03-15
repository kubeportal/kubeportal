from drf_spectacular.utils import extend_schema, extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import generics, serializers
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.middleware import csrf
from django.conf import settings

from kubeportal.api.views.tools import get_kubeportal_version


class BootstrapLinksSerializer(serializers.Serializer):
    login_url = serializers.URLField()
    logout_url = serializers.URLField()
    login_google_url = serializers.URLField()

class BootstrapInfoSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()
    links = BootstrapLinksSerializer()

class BootstrapInfoView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]  # Override default JWT auth
    serializer_class = BootstrapInfoSerializer

    @extend_schema(
        summary="Get bootstrap informations for talking to the API."
    )
    def get(self, request, version):
        instance = BootstrapInfoSerializer({
            "csrf_token": csrf.get_token(request),
            "links": {
                "login_url": reverse(viewname='rest_login', request=request),
                "logout_url": reverse(viewname='rest_logout', request=request),
                "login_google_url": reverse(viewname='api_google_login', request=request)
            }
        })
        return Response(instance.data)


