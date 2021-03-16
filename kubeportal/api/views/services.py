from drf_spectacular.utils import extend_schema, extend_schema_serializer, OpenApiExample
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api

import logging
logger = logging.getLogger('KubePortal')


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
    target_port = serializers.IntegerField(read_only=True)
    protocol = serializers.ChoiceField(choices=("TCP", "UDP"))


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

    @extend_schema(
        summary="Get service by its UID."
    )
    def get(self, request, version, uid):
        service = api.get_service(uid)

        if not request.user.has_namespace(service.metadata.namespace):
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{service.metadata.namespace}' of service '{service.metadata.uid}'. Access denied.")
            raise NotFound

        instance = ServiceSerializer({
            'name': service.metadata.name,
            'creation_timestamp': service.metadata.creation_timestamp,
            'type': service.spec.type,
            'selector': {'key': list(service.spec.selector.keys())[0],
                         'value': list(service.spec.selector.values())[0]},
            'ports': [{'port': item.port, 'target_port': item.target_port, 'protocol': item.protocol} for item in
                      service.spec.ports]
        })
        return Response(instance.data)


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
