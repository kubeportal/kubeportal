from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.middleware import csrf
from django.conf import settings

from kubeportal.api.views.tools import get_kubeportal_version


class BootstrapInfoView(GenericAPIView):
    permission_classes = [AllowAny]  # Override default JWT auth

    @extend_schema(
        operation={
            "operationId": "get_bootstrapinfo",
            "tags": ["api"],
            "summary": "Get bootstrap information for talking to the API.",
            "security": [{"jwtAuth": []}, {}],
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "csrf_token": {
                                        "type": "string",
                                        "example": "OIiIQkMv5xGfrI75GDAfnm1C1BPxxWlyMgUudmaTBaNKmtulGpSCWQje8uWrQjsb"
                                    },
                                    "portal_version": {
                                        "type": "string",
                                        "example": "v1.5.0"
                                    },
                                    "default_api_version": {
                                        "type": "string",
                                        "example": "v2.0.0"
                                    }}}}}}}})
    def get(self, request):
        return Response({
            'csrf_token': csrf.get_token(request),
            'portal_version': get_kubeportal_version(),
            'default_api_version': settings.API_VERSION
        })
