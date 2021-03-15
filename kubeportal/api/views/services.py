from drf_spectacular.utils import extend_schema, extend_schema_serializer, OpenApiExample
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


class SelectorSerializer(serializers.Serializer):
    """
    The API serializer for a label selector.
    """
    key = serializers.CharField()
    value = serializers.CharField()


class PortSerializer(serializers.Serializer):
    """
    The API serializer for a port definition.
    """
    port = serializers.IntegerField()
    protocol = serializers.ChoiceField(
        choices=("TCP", "UDP")
    )

class ServiceSerializer(serializers.Serializer):
    """
    The API serializer for a service defition.
    """
    name = serializers.CharField()
    creation_timestamp = serializers.DateTimeField(read_only=True)
    type = serializers.ChoiceField(
        choices=("NodePort", "ClusterIP", "LoadBalancer")
    )
    selector = SelectorSerializer()
    ports = serializers.ListField(child=PortSerializer())


class ServiceRetrievalView(generics.RetrieveAPIView):
    serializer_class = ServiceSerializer

class ServiceCreationView(generics.CreateAPIView):
    serializer_class = ServiceSerializer

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
