from django.middleware import csrf
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


class BootstrapInfoSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()
    login_url = serializers.URLField()
    logout_url = serializers.URLField()
    login_google_url = serializers.URLField()


class BootstrapInfoView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]  # Override default JWT auth
    serializer_class = BootstrapInfoSerializer

    @extend_schema(
        summary="Get bootstrap informations for talking to the API."
    )
    def get(self, request, version):
        instance = BootstrapInfoSerializer({
            "csrf_token": csrf.get_token(request),
            "login_url": reverse(viewname='rest_login', request=request),
            "logout_url": reverse(viewname='rest_logout', request=request),
            "login_google_url": reverse(viewname='api_google_login', request=request)
        })
        return Response(instance.data)
