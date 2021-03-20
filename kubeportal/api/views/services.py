from drf_spectacular.utils import extend_schema, extend_schema_serializer, OpenApiExample
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

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
    puid = serializers.CharField(read_only=True)
    creation_timestamp = serializers.DateTimeField(read_only=True)
    type = serializers.ChoiceField(
        choices=("NodePort", "ClusterIP", "LoadBalancer")
    )
    selector = SelectorSerializer()
    ports = serializers.ListField(child=PortSerializer())

class ServiceListSerializer(serializers.Serializer):
    service_urls = serializers.ListField(child=serializers.URLField())

class ServiceRetrievalView(generics.RetrieveAPIView):
    serializer_class = ServiceSerializer

    @extend_schema(
        summary="Get service by its UID."
    )
    def get(self, request, version, puid):
        namespace, name = puid.split('_')
        service = api.get_namespaced_service(namespace, name)

        if not request.user.has_namespace(service.metadata.namespace):
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{service.metadata.namespace}' of service '{service.metadata.uid}'. Access denied.")
            raise NotFound

        if service.spec.selector:
            selector = {'key': list(service.spec.selector.keys())[0],
                        'value': list(service.spec.selector.values())[0]} 
        else:
            selector = None

        instance = ServiceSerializer({
            'name': service.metadata.name,
            'puid': service.metadata.namespace + '_' + service.metadata.name,
            'creation_timestamp': service.metadata.creation_timestamp,
            'type': service.spec.type,
            'selector': selector,
            'ports': [{'port': item.port, 'target_port': item.target_port, 'protocol': item.protocol} for item in
                      service.spec.ports]
        })
        return Response(instance.data)


class ServicesView(generics.CreateAPIView, generics.RetrieveAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return ServiceListSerializer
        if self.request.method == "POST":
            return ServiceSerializer


    @extend_schema(
        summary="Get the list of services in a namespace.",
        request=None,
        responses=ServiceListSerializer
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            services = api.get_namespaced_services(namespace)
            puids = [item.metadata.namespace + '_' + item.metadata.name for item in services]
            instance = ServiceListSerializer({
                'service_urls': [reverse(viewname='service_retrieval', kwargs={'puid': puid}, request=request) for puid in puids]
            })
            return Response(instance.data)
        else:
            raise NotFound

    @extend_schema(
        summary="Create service in a namespace.",
        request = ServiceSerializer,
        responses = None
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
