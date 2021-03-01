from drf_spectacular.utils import extend_schema, extend_schema_serializer, OpenApiExample
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'NodePort example',
            value={
                'name': 'my-service',
                'type': 'NodePort',
                'selector': {'key': 'app', 'value': 'kubeportal'},
                'ports': [{'port': 8000, 'protocol': 'TCP'}]
            },
        ),
        OpenApiExample(
            'ClusterIP example',
            value={
                'name': 'my-service',
                'type': 'ClusterIP',
                'selector': {'key': 'app', 'value': 'kubeportal'},
                'ports': [{'port': 8000, 'protocol': 'TCP'}]
            },
        ),
        OpenApiExample(
            'LoadBalancer example',
            value={
                'name': 'my-service',
                'type': 'LoadBalancer',
                'selector': {'key': 'app', 'value': 'kubeportal'},
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


class ServicesView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer

    @extend_schema(
        summary="Get services in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(api.get_namespaced_services(namespace))
        else:
            raise NotFound

    @extend_schema(
        summary="Create service in a namespace."
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_service(namespace,
                                   request.data["name"],
                                   request.data["type"],
                                   request.data["selector"],
                                   request.data["ports"])
            return Response(status=201)
        else:
            raise NotFound
