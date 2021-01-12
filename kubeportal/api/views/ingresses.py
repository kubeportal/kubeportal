from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_serializer
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response
from kubeportal.k8s import kubernetes_api as api


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'HTTPS Ingress example',
            value={
                'name': 'my-ingress',
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                },
                'tls': True,
                'rules': {
                    'www.example.com': {
                        '/svc': {
                            'service_name': 'my-svc',
                            'service_port': 8000
                        },
                        '/docs': {
                            'service_name': 'my-docs-svc',
                            'service_port': 5000
                        }
                    }
                }
            },
        ),
    ]
)
class IngressSerializer(serializers.Serializer):
    name = serializers.CharField()
    annotations = serializers.DictField()
    tls = serializers.BooleanField()
    rules = serializers.ListField()
    creation_timestamp = serializers.DateTimeField(read_only=True)


class IngressViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingresses in a namespace."
    )
    def list(self, request, version):
        return Response(request.user.k8s_ingresses())

    @extend_schema(
        summary="Create an ingress in a namespace."
    )
    def create(self, request, version):
        api.create_k8s_ingress(request.user.k8s_namespace().name,
                               request.data["name"],
                               request.data["annotations"],
                               request.data["tls"],
                               request.data["rules"]
                               )
        return Response(status=201)
