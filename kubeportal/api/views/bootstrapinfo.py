from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
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
                                    "links": {
                                        "type": "object",
                                        "properties": {
                                            "login": {
                                                "type": "string",
                                                "example": "http://testserver/api/v2.0.0/login/"
                                            },
                                            "login_google": {
                                                "type": "string",
                                                "example": "http://testserver/api/v2.0.0/login_google/"
                                            }
                                        }
                                    }}}}}}}})
    def get(self, request, version):
        return Response({
            'csrf_token': csrf.get_token(request),
            'links': {
                'login': reverse(viewname='rest_login', request=request),
                'login_google': reverse(viewname='api_google_login', request=request),
            }
        })
