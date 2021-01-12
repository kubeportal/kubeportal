from drf_spectacular.utils import extend_schema, extend_schema_serializer, OpenApiExample
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response
from kubeportal.k8s import kubernetes_api as api


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'NodePort example',
            value={
                'name': 'my-service',
                'type': 'NodePort',
                'selector': {'app': 'kubeportal'},
                'ports': [{'port': 8000, 'protocol': 'TCP'}]
            },
        ),
        OpenApiExample(
            'ClusterIP example',
            value={
                'name': 'my-service',
                'type': 'ClusterIP',
                'selector': {'app': 'kubeportal'},
                'ports': [{'port': 8000, 'protocol': 'TCP'}]
            },
        ),
        OpenApiExample(
            'LoadBalancer example',
            value={
                'name': 'my-service',
                'type': 'LoadBalancer',
                'selector': {'app': 'kubeportal'},
                'ports': [{'port': 8000, 'protocol': 'TCP'}]
            },
        ),
    ]
)
class ServiceSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.ChoiceField(
        choices=("NodePort", "ClusterIP", "LoadBalancer")
    )
    selector = serializers.DictField(
        allow_empty=False
    )
    ports = serializers.ListField(
        child=serializers.DictField(
            allow_empty=False
        ),
        allow_empty=False)
    creation_timestamp = serializers.DateTimeField(read_only=True)


class ServiceViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ServiceSerializer

    @extend_schema(
        summary="Get services in a namespace."
    )
    def list(self, request, version):
        return Response(request.user.k8s_services())

    @extend_schema(
        summary="Create service in a namespace."
    )
    def create(self, request, version):
        api.create_k8s_service(request.user.k8s_namespace().name,
                               request.data["name"],
                               request.data["type"],
                               request.data["selector"],
                               request.data["ports"])
        return Response(status=201)
