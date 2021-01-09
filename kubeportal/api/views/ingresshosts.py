from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from kubeportal.k8s import kubernetes_api as api


class IngressHostsView(GenericAPIView):

    @extend_schema(
        operation={
            "operationId": "get_ingresshosts",
            "tags": ["api"],
            "summary": "Get the list of host names used by ingresses.",
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "example": "app.example.com"
                                    }
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request, version):
        return Response(api.get_ingress_hosts())
