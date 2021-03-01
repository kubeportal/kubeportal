from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_serializer
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'HTTPS Ingress example',
            value={
                'name': 'my-ingress',
                'annotations': [
                    {'key': 'nginx.ingress.kubernetes.io/rewrite-target', 'value': '/'}
                ],
                'tls': True,
                'rules': [
                    {'host': 'www.example.com',
                     'paths': [
                         {'path': '/svc',
                          'service_name': 'my-svc',
                          'service_port': 8000
                          },
                         {'path': '/docs',
                          'service_name': 'my-docs-svc',
                          'service_port': 5000
                          }
                     ]
                     }
                ]
            }
        ),
    ]
)
class IngressSerializer(serializers.Serializer):
    name = serializers.CharField()
    annotations = serializers.DictField()
    tls = serializers.BooleanField()
    rules = serializers.ListField()
    creation_timestamp = serializers.DateTimeField(read_only=True)


class IngressesView(generics.ListCreateAPIView):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingresses in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(api.get_namespaced_ingresses(namespace))
        else:
            # https://lockmedown.com/when-should-you-return-404-instead-of-403-http-status-code/
            raise NotFound

    @extend_schema(
        summary="Create an ingress in a namespace."
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_ingress(namespace,
                                   request.data["name"],
                                   request.data["annotations"],
                                   request.data["tls"],
                                   request.data["rules"]
                                   )
            return Response(status=201)
        else:
            raise NotFound
